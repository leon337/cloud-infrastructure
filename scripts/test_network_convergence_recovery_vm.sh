#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
readonly ROOT
readonly CONFIRM=MCF_NETWORK_CONVERGENCE_KVM_ONLY
readonly OP="$ROOT/automation/mission-001/operations/recover-network-convergence"
CANDIDATE=$(git -C "$ROOT" rev-parse HEAD)
readonly CANDIDATE

fail() { printf 'NETWORK_CONVERGENCE_VM_FAIL reason=%s\n' "$1" >&2; exit 1; }
[[ ${NETWORK_CONVERGENCE_KVM_CONFIRM:-} == "$CONFIRM" ]] || fail confirmation_required
[[ $(hostname --short) == mcf-f1-2c-kvm-* ]] || fail wrong_guest
[[ -x $OP ]] || fail operation_not_executable

sudo ip link del eth0 2>/dev/null || true
sudo ip link del mcfgw0 2>/dev/null || true
sudo rm -f /etc/netplan/55-mcf-network-convergence-fixture.yaml \
  /etc/netplan/60-cloud-infrastructure-network-convergence.yaml
sudo rm -rf /var/lib/cloud-platform-network-convergence-p2
sudo rm -f /run/lock/cloud-platform-network-convergence-p2.lock
sudo ip link add eth0 type veth peer name mcfgw0
sudo ip link set mcfgw0 up
sudo ip addr add 169.58.128.1/17 dev mcfgw0
cat <<'YAML' | sudo tee /etc/netplan/55-mcf-network-convergence-fixture.yaml >/dev/null
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - 169.58.171.192/17
      routes:
        - to: default
          via: 169.58.128.1
YAML
sudo chmod 600 /etc/netplan/55-mcf-network-convergence-fixture.yaml
cat <<'CRON' | sudo tee /etc/cron.d/staticroute >/dev/null
@reboot root ip route replace $(ip route list dev eth0 scope link | head -n1 | awk '{ print $1 }') via $(ip route list dev eth0 | awk '/default/{ print $3 }') dev eth0 &>/dev/null
CRON
sudo chmod 644 /etc/cron.d/staticroute
printf '%s\n' MCF_NETWORK_CONVERGENCE_KVM_V1 | sudo tee /etc/mcf-network-convergence-kvm >/dev/null
sudo chmod 600 /etc/mcf-network-convergence-kvm
cat <<'BACKUP' | sudo tee /usr/local/sbin/cloud-infrastructure-config-backup >/dev/null
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' KVM_BACKUP_PASS
BACKUP
sudo chmod 755 /usr/local/sbin/cloud-infrastructure-config-backup

sudo netplan generate
sudo networkctl reload
sudo ip link set eth0 up
sudo networkctl reconfigure eth0
for _ in $(seq 1 40); do
  networkctl status eth0 --json=short | grep -Fq '"AdministrativeState":"configured"' && break
  sleep 0.25
done
networkctl status eth0 --json=short | grep -Fq '"AdministrativeState":"configured"' || fail fixture_not_configured
ip -4 route show 169.58.128.0/17 dev eth0 | grep -q . || fail connected_route_initially_missing
sudo ip route del 169.58.128.0/17 dev eth0
sudo systemctl restart systemd-networkd
sleep 2
networkctl status eth0 --json=short | grep -Fq '"AdministrativeState":"configuring"' || fail broken_state_not_reproduced
echo ADMIN_STATE=configuring
set +e
timeout 3 /lib/systemd/systemd-networkd-wait-online -i eth0:degraded >/dev/null 2>&1
broken_rc=$?
set -e
[[ $broken_rc -eq 124 ]] || fail wait_broken_did_not_timeout
echo WAIT_BROKEN_RC=124

pre_netplan_hash=$(sudo sha256sum /etc/netplan/50-cloud-init.yaml | awk '{print $1}')
pre_generated_hash=$(sudo sha256sum /run/systemd/network/10-netplan-eth0.network | awk '{print $1}')
pre_staticroute_hash=$(sudo sha256sum /etc/cron.d/staticroute | awk '{print $1}')

ENV=(
  NETWORK_CONVERGENCE_TEST_CONFIRM=NETWORK_CONVERGENCE_DISPOSABLE_KVM_ONLY
  NETWORK_CONVERGENCE_CANDIDATE_SHA="$CANDIDATE"
)
sudo env "${ENV[@]}" "$OP" precheck
sudo env "${ENV[@]}" "$OP" apply
CHECKPOINT=/var/lib/cloud-platform-network-convergence-p2/checkpoint
sudo grep -Fxq "netplan_sha256=$pre_netplan_hash" "$CHECKPOINT" || fail checkpoint_netplan_hash_mismatch
sudo grep -Fxq "generated_sha256=$pre_generated_hash" "$CHECKPOINT" || fail checkpoint_generated_hash_mismatch
sudo grep -Fxq "staticroute_sha256=$pre_staticroute_hash" "$CHECKPOINT" || fail checkpoint_staticroute_hash_mismatch
echo checkpoint_hashes_match=PASS
sudo env "${ENV[@]}" "$OP" check
networkctl status eth0 --json=short | grep -Fq '"AdministrativeState":"configured"' || fail recovery_not_configured
echo ADMIN_STATE=configured
timeout 5 /lib/systemd/systemd-networkd-wait-online -i eth0:degraded >/dev/null 2>&1 || fail wait_recovered_failed
echo WAIT_RECOVERED_RC=0
ip -4 route show 169.58.128.1/32 dev eth0 | grep -q 'scope link' || fail host_route_missing_after_apply
! ip -4 route show 169.58.128.0/17 dev eth0 | grep -q . || fail connected_route_restored_unexpectedly

sudo env "${ENV[@]}" "$OP" rollback
sudo systemctl restart systemd-networkd
sleep 2
echo ROLLBACK_RUNTIME_REEVALUATED
set +e
timeout 3 /lib/systemd/systemd-networkd-wait-online -i eth0:degraded >/dev/null 2>&1
rollback_rc=$?
set -e
[[ $rollback_rc -eq 124 ]] || fail wait_rollback_did_not_timeout
echo WAIT_ROLLBACK_RC=124
networkctl status eth0 --json=short | grep -Fq '"AdministrativeState":"configuring"' || fail rollback_not_configuring
echo ADMIN_STATE=configuring
[[ ! -e /etc/netplan/60-cloud-infrastructure-network-convergence.yaml ]] || fail overlay_left_after_rollback
! ip -4 route show 169.58.128.1/32 dev eth0 | grep -q . || fail host_route_left_after_rollback
printf 'NETWORK_CONVERGENCE_VM_PASS candidate=%s\n' "$CANDIDATE"
