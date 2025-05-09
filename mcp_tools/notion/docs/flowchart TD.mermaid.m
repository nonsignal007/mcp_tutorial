flowchart TD
    A[Chat Interface] --> B{Claude Processing Layer}
    
    subgraph Storage Layer
        C[Knowledge Graph]
        D[(SQLite)]
        E[Obsidian Vault]
        F[Notion Workspace]
    end
    
    B --> C
    B --> D
    B --> E
    B --> F
    
    subgraph Specialized Functions
        D --> G[Quick Lookup Cache]
        D --> H[Relationship Indices]
        
        E --> I[Local Markdown Files]
        E --> J[Graph Visualization]
        
        F --> K[Structured Lists]
        F --> L[Rich Documents]
        
        C --> M[Context Memory]
        C --> N[Relationship Web]
    end
    
    M --> B
    N --> B
    G --> B
    J --> B
    
    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style C fill:#bfb,stroke:#333
    style D fill:#fbf,stroke:#333