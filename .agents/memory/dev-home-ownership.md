---
name: Ownership della home dev
description: Vincolo sull'ordine di creazione delle directory XDG usate dagli installer CLI.
---

Non creare `/home/dev/.local` o suoi discendenti durante la fase `root` del Containerfile. Le directory sotto `.local` devono essere create dopo `USER dev`.

**Why:** La creazione di un discendente con `install -d` nella fase root può lasciare il genitore `.local` come `root:root`; l'installer nativo di Claude fallisce quando prova a creare `.local/state`.

**How to apply:** Quando si aggiungono cache, stato o dati persistenti sotto `/home/dev/.local`, inserirli nel blocco `RUN mkdir -p` successivo a `USER dev`, senza anticiparne la creazione.