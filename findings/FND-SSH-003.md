# FND-SSH-003 — Login SSH atual da conta ubuntu

Status: **RESOLVED em 15/08/2026**. Severidade histórica: **HIGH** enquanto bloqueava a validação de um acesso administrativo alternativo.

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

## Resolução — 15/08/2026

A chave privada local correspondente à chave antiga estava protegida por passphrase, e LEANDRO não dispunha dessa passphrase. A verificação local segura mostrou que `ssh-agent`/keyring não disponibilizava nenhuma identidade utilizável. Isso constituiu um bloqueador local concreto para concluir o teste com aquela chave; não prova defeito no servidor nem explica necessariamente todas as tentativas históricas.

Não houve tentativa de recuperar, extrair, adivinhar, quebrar ou expor a passphrase antiga. Foi criada uma nova chave ED25519 dedicada, com fingerprint pública `SHA256:/p5jX65s2WyxkD3xooTozV09DSYAmKIAgZKk3Veb1Hg`.

A nova chave pública foi **adicionada**, não substituída. A chave antiga permaneceu presente. O arquivo `authorized_keys` continuou pertencendo a `ubuntu:ubuntu`, modo `600`, e a nova chave ficou presente exatamente uma vez.

O login atual como `ubuntu` foi validado usando exclusivamente autenticação `publickey`, com fallback para senha desativado durante o teste. O resultado confirmou usuário `ubuntu`, UID `1000` e hostname `vmi3506102`. Nenhuma mudança de política do SSH foi necessária para validar o novo acesso; root/senha também permaneceu preservado.
