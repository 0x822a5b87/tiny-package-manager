# tiny-package-manager
A tiny package manager for trying my hand at Python.

## TEST

```bash
uv run pytest -v
```

## DESCRIPTION

## ANALYSING DEPENDENCIES

First of all, we must make it clear what the differences between `direct dependencies` and `indirect dependencies` are. Here is a simple example:

```mermaid
---
title: dependencies
---
flowchart LR

jest("jest-0.0.71"):::green

express-resource("express-resource-*"):::purple
underscore("underscore-*"):::purple
sji("sji-*"):::purple

indirect01("indirect dependency ..."):::animate

jest --> express-resource --> indirect01
jest --> underscore --> indirect01
jest --> sji --> indirect01


classDef pink 1,fill:#FFCCCC,stroke:#333, color: #fff, font-weight:bold;
classDef green fill: #696,color: #fff,font-weight: bold;
classDef purple fill:#969,stroke:#333, font-weight: bold;
classDef error fill:#bbf,stroke:#f66,stroke-width:2px,color:#fff,stroke-dasharray: 5 5
classDef coral fill:#f9f,stroke:#333,stroke-width:4px;
classDef animate stroke-dasharray: 9,5,stroke-dashoffset: 900,animation: dash 25s linear infinite;
```



We can start our incremental parse now. The solution is quite simple:

1. We have `available`, `unresolved`. At the beginning, available is empty and unresolved is equal to  all direct dependencies.
2. Download all direct dependencies and then analyse their dependencies; tshe results are new unresolved dependencies.
3. Keep analysing unresolved dependencies until they become empty, which means the resolution is complete; or we may encounter errors like version conflicts, which means the resolution has failed.

## ARE ALL DEPENDENCIES  FINISHED?

> `((A, 3), (B, 3), (C, 3))` ， our goal is to check whether the version is legal.

```json
{
  "A": {
    "3": {"B": ["3", "2"], "C": ["2"]},
    "2": {"B": ["2"],      "C": ["2", "1"]},
    "1": {"B": ["1"]}
  },
  "B": {
    "3": {"C": ["2"]},
    "2": {"C": ["1"]},
    "1": {"C": ["1"]}
  },
  "C": {
    "2": [],
    "1": []
  }
}
```

```mermaid
---
title: Original Dependencies
---
flowchart LR

A3("A3"):::green
A2("A2"):::green
A1("A1"):::green

B3("B3"):::purple
B2("B2"):::purple
B1("B1"):::purple

C2("C2"):::pink
C1("C1"):::pink

A3 --> B3
A3 --> B2
A3 --> C2

A2 --> B2
A2 --> C2
A2 --> C1

A1 --> B1

B3 --> C2
B2 --> C1
B1 --> C1

classDef pink 1,fill:#FFCCCC,stroke:#333, color: #fff, font-weight:bold;
classDef green fill: #696,color: #fff,font-weight: bold;
classDef purple fill:#969,stroke:#333, font-weight: bold;
classDef error fill:#bbf,stroke:#f66,stroke-width:2px,color:#fff,stroke-dasharray: 5 5
```

```mermaid
---
title: Dependencies after merging duplicate
---
flowchart LR

A3("A3"):::green
A2("A2"):::green
A1("A1"):::green

B3("B3"):::purple
B2("B2"):::purple
B1("B1"):::purple

C2("C2"):::pink
C1("C1"):::pink

A3 --> B3
A3 --> B2

A2 --> B2
A2 --> C2

A1 --> B1

B3 --> C2
B2 --> C1
B1 --> C1

classDef pink 1,fill:#FFCCCC,stroke:#333, color: #fff, font-weight:bold;
classDef green fill: #696,color: #fff,font-weight: bold;
classDef purple fill:#969,stroke:#333, font-weight: bold;
classDef error fill:#bbf,stroke:#f66,stroke-width:2px,color:#fff,stroke-dasharray: 5 5
```
