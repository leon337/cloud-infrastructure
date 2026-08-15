# FND-SSH-003 — Login SSH atual da conta ubuntu não validado

Status: **CONFIRMED — OPEN**. Severidade: **HIGH** por bloquear a substituição segura do acesso root.

## Evidência de 15/08/2026

- a conta `ubuntu` existe, está bloqueada para senha e possui shell `/bin/bash`;
- `authorized_keys` existe com proprietário/permissões coerentes;
- sua única chave ED25519 tem fingerprint `SHA256:FeamXuFKDiA868c9eKVH8AOMXOQMLL1KBNH4Y9DrqMU`;
- essa fingerprint coincide com a chave pública local dedicada;
- o servidor aceitou a oferta da chave, mas a autenticação por chave não foi concluída;
- o cliente caiu para senha, que falhou porque a conta tem senha bloqueada.

Há um login histórico por chave aceito para `ubuntu` em 14/08/2026, mas ele não substitui a validação atual.

## Limite probatório

A causa exata não foi diagnosticada. Não afirmar erro de passphrase, chave inválida ou defeito do servidor sem nova microchecagem autorizada.

