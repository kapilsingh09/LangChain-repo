import json, os

base = "/mnt/data/hybrid_rag_dataset"
os.makedirs(base, exist_ok=True)

entities = [
    {"id":"COMP-001","type":"Company","name":"Nexus Corporation","aliases":["Nexus","NexusCorp"]},
    {"id":"COMP-002","type":"Company","name":"Vertex Financial Services","aliases":["Vertex Financial","Vertex"]},
    {"id":"COMP-003","type":"Company","name":"Orbit Retail Systems","aliases":["Orbit Retail","Orbit"]},
    {"id":"LOC-001","type":"Location","name":"Seattle Technology Center","aliases":["Seattle Hub","SEA-1"]},
    {"id":"LOC-002","type":"Location","name":"New York Operations Center","aliases":["NY Operations","NYC Hub"]},
    {"id":"LOC-003","type":"Location","name":"Austin Engineering Office","aliases":["Austin Office","AUS-1"]},
    {"id":"DEPT-001","type":"Department","name":"Cloud Engineering","aliases":["Cloud Eng","CE"]},
    {"id":"DEPT-002","type":"Department","name":"Data Platforms","aliases":["Data Platform","DP"]},
    {"id":"DEPT-003","type":"Department","name":"Security Engineering","aliases":["Security Eng","SE"]},
    {"id":"EMP-001","type":"Employee","name":"Alex Mercer","aliases":["A. Mercer","Alex M."]},
    {"id":"EMP-002","type":"Employee","name":"Priya Sharma","aliases":["P. Sharma","Priya"]},
    {"id":"EMP-003","type":"Employee","name":"Daniel Kim","aliases":["D. Kim","Daniel"]},
    {"id":"EMP-004","type":"Employee","name":"Maria Lopez","aliases":["M. Lopez","Maria"]},
    {"id":"EMP-005","type":"Employee","name":"Ethan Brooks","aliases":["E. Brooks","Ethan"]},
    {"id":"PROJ-001","type":"Project","name":"Project Aether","aliases":["Aether","Aether-v1"]},
    {"id":"PROJ-002","type":"Project","name":"Project Borealis","aliases":["Borealis","Borealis Service"]},
    {"id":"PROJ-003","type":"Project","name":"Project Cygnus","aliases":["Cygnus","Cygnus Analytics"]},
    {"id":"PROJ-004","type":"Project","name":"Project Delta","aliases":["Delta","Delta Shield"]},
    {"id":"TECH-001","type":"Technology","name":"PostgreSQL","aliases":["Postgres","PG"]},
    {"id":"TECH-002","type":"Technology","name":"Kubernetes","aliases":["K8s","Kube"]},
    {"id":"TECH-003","type":"Technology","name":"Apache Kafka","aliases":["Kafka"]},
    {"id":"TECH-004","type":"Technology","name":"Redis","aliases":["Redis Cache"]},
    {"id":"TECH-005","type":"Technology","name":"FastAPI","aliases":["Fast API"]},
    {"id":"PROD-001","type":"Product","name":"NexusDataStream","aliases":["DataStream","NDS"]},
    {"id":"PROD-002","type":"Product","name":"NexusRiskEngine","aliases":["Risk Engine","NRE"]},
    {"id":"CUST-001","type":"Customer","name":"FinGlobal Inc.","aliases":["FinGlobal","FG"]},
    {"id":"CUST-002","type":"Customer","name":"Mercury Health","aliases":["Mercury","Mercury Health Systems"]},
    {"id":"CUST-003","type":"Customer","name":"Atlas Logistics","aliases":["Atlas","Atlas Logistics Ltd."]},
]

relationships = [
    {"source":"DEPT-001","type":"BELONGS_TO","target":"COMP-001","source_documents":["DOC-004"]},
    {"source":"DEPT-001","type":"LOCATED_IN","target":"LOC-001","source_documents":["DOC-004"]},
    {"source":"DEPT-002","type":"BELONGS_TO","target":"COMP-001","source_documents":["DOC-006"]},
    {"source":"DEPT-002","type":"LOCATED_IN","target":"LOC-003","source_documents":["DOC-006"]},
    {"source":"DEPT-003","type":"BELONGS_TO","target":"COMP-001","source_documents":["DOC-010"]},
    {"source":"DEPT-003","type":"LOCATED_IN","target":"LOC-002","source_documents":["DOC-010"]},
    {"source":"EMP-001","type":"WORKS_AT","target":"COMP-001","source_documents":["DOC-001"]},
    {"source":"EMP-001","type":"BELONGS_TO","target":"DEPT-001","source_documents":["DOC-004"]},
    {"source":"EMP-001","type":"MANAGES","target":"PROJ-001","source_documents":["DOC-001"]},
    {"source":"EMP-002","type":"WORKS_AT","target":"COMP-001","source_documents":["DOC-002"]},
    {"source":"EMP-002","type":"BELONGS_TO","target":"DEPT-002","source_documents":["DOC-006"]},
    {"source":"EMP-002","type":"WORKS_ON","target":"PROJ-002","source_documents":["DOC-002"]},
    {"source":"EMP-002","type":"WORKS_ON","target":"PROJ-001","source_documents":["DOC-011"]},
    {"source":"EMP-003","type":"WORKS_AT","target":"COMP-001","source_documents":["DOC-007"]},
    {"source":"EMP-003","type":"BELONGS_TO","target":"DEPT-002","source_documents":["DOC-006"]},
    {"source":"EMP-003","type":"WORKS_ON","target":"PROJ-003","source_documents":["DOC-007"]},
    {"source":"EMP-003","type":"MANAGES","target":"PROJ-003","source_documents":["DOC-007"]},
    {"source":"EMP-004","type":"WORKS_AT","target":"COMP-001","source_documents":["DOC-009"]},
    {"source":"EMP-004","type":"BELONGS_TO","target":"DEPT-003","source_documents":["DOC-010"]},
    {"source":"EMP-004","type":"WORKS_ON","target":"PROJ-004","source_documents":["DOC-009"]},
    {"source":"EMP-005","type":"WORKS_AT","target":"COMP-001","source_documents":["DOC-008"]},
    {"source":"EMP-005","type":"BELONGS_TO","target":"DEPT-001","source_documents":["DOC-004"]},
    {"source":"EMP-005","type":"WORKS_ON","target":"PROJ-002","source_documents":["DOC-008"]},
    {"source":"PROJ-001","type":"USES","target":"TECH-001","source_documents":["DOC-001"]},
    {"source":"PROJ-001","type":"USES","target":"TECH-004","source_documents":["DOC-001"]},
    {"source":"PROJ-001","type":"PRODUCES","target":"PROD-001","source_documents":["DOC-004"]},
    {"source":"PROJ-002","type":"DEPENDS_ON","target":"PROJ-001","source_documents":["DOC-002"]},
    {"source":"PROJ-002","type":"USES","target":"TECH-002","source_documents":["DOC-002"]},
    {"source":"PROJ-002","type":"USES","target":"TECH-005","source_documents":["DOC-008"]},
    {"source":"PROJ-002","type":"SERVES","target":"CUST-001","source_documents":["DOC-003"]},
    {"source":"PROJ-003","type":"USES","target":"TECH-003","source_documents":["DOC-007"]},
    {"source":"PROJ-003","type":"USES","target":"TECH-001","source_documents":["DOC-007"]},
    {"source":"PROJ-003","type":"PRODUCES","target":"PROD-002","source_documents":["DOC-012"]},
    {"source":"PROJ-003","type":"SERVES","target":"CUST-002","source_documents":["DOC-012"]},
    {"source":"PROJ-004","type":"DEPENDS_ON","target":"PROJ-002","source_documents":["DOC-009"]},
    {"source":"PROJ-004","type":"USES","target":"TECH-002","source_documents":["DOC-009"]},
    {"source":"PROJ-004","type":"SERVES","target":"CUST-003","source_documents":["DOC-013"]},
    {"source":"PROD-001","type":"USED_BY","target":"CUST-001","source_documents":["DOC-003"]},
    {"source":"PROD-002","type":"USED_BY","target":"CUST-002","source_documents":["DOC-012"]},
    {"source":"DEPT-001","type":"MAINTAINS","target":"TECH-001","source_documents":["DOC-005"]},
    {"source":"DEPT-001","type":"MAINTAINS","target":"TECH-002","source_documents":["DOC-005"]},
    {"source":"DEPT-002","type":"MAINTAINS","target":"TECH-003","source_documents":["DOC-006"]},
    {"source":"DEPT-002","type":"MAINTAINS","target":"TECH-001","source_documents":["DOC-006"]},
    {"source":"DEPT-003","type":"MAINTAINS","target":"TECH-002","source_documents":["DOC-010"]},
]

documents = [
    {"document_id":"DOC-001","title":"Architecture Review: Project Aether","metadata":{"department":"Cloud Engineering","year":2026},"content":
     "Project Aether is a core data service operated by Nexus Corporation. The architecture review records that Alex Mercer, often referenced internally as A. Mercer, is the engineering manager responsible for Aether. The service uses PostgreSQL as its primary relational datastore and Redis for low-latency caching. The team selected PostgreSQL because transactional consistency is important for the service. Redis is used for frequently accessed configuration and session information. Aether is maintained by the Cloud Engineering organization at Nexus. The architecture group describes Aether as the foundation for several downstream services, although this document does not enumerate every dependency. The review also notes that the service exposes internal APIs used by other Nexus teams. During the review, engineers emphasized that the database layer and cache should remain independently scalable. The Seattle Technology Center is the main collaboration location for the Cloud Engineering group. Alex Mercer approved the current architecture after the reliability review."},
    {"document_id":"DOC-002","title":"Borealis Service Integration Strategy","metadata":{"department":"Cloud Engineering","year":2026},"content":
     "Project Borealis is an application service at Nexus Corporation. Priya Sharma, also called P. Sharma or simply Priya in internal notes, works on the Borealis engineering team. Borealis depends on Project Aether for several shared data capabilities rather than maintaining a separate copy of those services. The integration strategy specifies Kubernetes as the deployment platform, with some engineers shortening the name to K8s. Borealis communicates with Aether through internal service APIs. The strategy states that changes to Aether interfaces must be reviewed before Borealis releases are promoted. Borealis is intended to support customer-facing workflows and is designed to scale horizontally. The service also uses FastAPI for selected internal API components. The document focuses on service integration and does not specify the identity provider, cloud vendor, or annual operating budget. Priya participates in integration testing and release validation."},
    {"document_id":"DOC-003","title":"FinGlobal Deployment Overview","metadata":{"customer":"FinGlobal Inc.","year":2026},"content":
     "FinGlobal Inc., frequently shortened to FinGlobal or FG, uses Nexus Corporation services for financial data workflows. Project Borealis serves FinGlobal customer workloads. The deployment overview explains that Borealis consumes shared capabilities from Project Aether. FinGlobal also uses the NexusDataStream product, commonly called DataStream or NDS, for selected streaming and reporting workflows. NexusDataStream is produced by Project Aether. The customer team receives operational notifications from the Borealis service, while DataStream provides event-oriented information used by downstream reporting systems. The document does not identify a cloud provider for either service. It also does not state employee compensation or individual customer contracts. FinGlobal's technical contacts coordinate release windows with the Nexus platform teams. The deployment is designed so that customer-specific workloads remain isolated from internal engineering environments."},
    {"document_id":"DOC-004","title":"Q3 Cloud Engineering Department Update","metadata":{"department":"Cloud Engineering","year":2026},"content":
     "The Cloud Engineering department, abbreviated as Cloud Eng or CE, belongs to Nexus Corporation, also known in older material as NexusCorp. The department is based at the Seattle Technology Center, sometimes called the Seattle Hub or SEA-1. Alex Mercer belongs to Cloud Engineering and leads the technical work around Project Aether. Ethan Brooks is also part of Cloud Engineering and contributes to Project Borealis. The department update records that Project Aether produces the NexusDataStream product, known internally as DataStream or NDS. Cloud Engineering is responsible for platform reliability and service operations. The update mentions that several engineers rotate between application and infrastructure duties. It does not contain salary information or detailed customer contract terms. Seattle remains the primary location for the group's platform meetings and architecture reviews."},
    {"document_id":"DOC-005","title":"Internal Technology Stack Audit","metadata":{"department":"Cloud Engineering","year":2026},"content":
     "The internal technology audit lists PostgreSQL and Kubernetes among the technologies maintained by Cloud Engineering. PostgreSQL is also called Postgres or PG, while Kubernetes is commonly shortened to K8s or Kube. The department maintains these platforms for multiple internal services. The audit confirms that Project Aether uses PostgreSQL and that Project Borealis uses Kubernetes. Engineers note that database maintenance and container platform maintenance are handled by separate operational rotations. The audit references Alex Mercer for architecture approvals but does not assign personal ownership of every technology. Cloud Engineering also maintains operational documentation for service deployment and incident response. The report intentionally excludes employee compensation data and does not identify the cloud provider used for each workload."},
    {"document_id":"DOC-006","title":"Data Platforms Organization and Operations","metadata":{"department":"Data Platforms","year":2026},"content":
     "Data Platforms is an engineering department within Nexus Corporation and operates from the Austin Engineering Office, also referred to as Austin Office or AUS-1. Priya Sharma belongs to Data Platforms and contributes to Project Borealis as well as cross-team data initiatives. Daniel Kim is another Data Platforms engineer and manages Project Cygnus. The department maintains Apache Kafka, usually called Kafka, for event streaming and PostgreSQL for analytical storage. The organization provides shared data infrastructure used by several Nexus projects. The report describes Kafka maintenance as a team responsibility rather than assigning it to one employee. It does not provide individual salaries or identify a specific cloud provider. Austin is the main location for the department's engineering operations and data-platform planning sessions."},
    {"document_id":"DOC-007","title":"Cygnus Analytics Architecture","metadata":{"project":"Project Cygnus","year":2026},"content":
     "Project Cygnus is an analytics platform managed by Daniel Kim of Nexus Corporation. Daniel Kim belongs to the Data Platforms department. Cygnus uses Apache Kafka for ingesting event streams and PostgreSQL for storing analytical datasets. The platform is designed to transform operational events into datasets consumed by internal analytics applications. The architecture team selected Kafka because multiple producers can publish events independently. PostgreSQL provides relational querying for downstream analysis. Cygnus produces the NexusRiskEngine product, also called the Risk Engine or NRE, which is used by Mercury Health. The architecture document describes Mercury Health as a customer of Nexus Corporation. It does not specify the cloud provider or Daniel Kim's compensation."},
    {"document_id":"DOC-008","title":"Borealis API Operations Runbook","metadata":{"project":"Project Borealis","year":2026},"content":
     "The Borealis operations runbook records that Ethan Brooks contributes to Project Borealis from the Cloud Engineering team. Borealis runs on Kubernetes and uses FastAPI for several API endpoints. The service depends on Project Aether for shared data capabilities. Operational procedures include deployment validation, API health checks, and rollback testing. The runbook notes that FastAPI components are packaged into containers managed by Kubernetes. Priya Sharma also participates in Borealis integration work, although the runbook is focused on operational procedures rather than team structure. The document does not identify the cloud vendor, customer pricing, or employee salaries. Engineers use the short name Kube when discussing the Kubernetes cluster in incident channels."},
    {"document_id":"DOC-009","title":"Delta Shield Security Project","metadata":{"project":"Project Delta","year":2026},"content":
     "Project Delta, also known as Delta Shield, is a security-oriented project at Nexus Corporation. Maria Lopez belongs to the Security Engineering department and works on Delta. The project uses Kubernetes for isolated service workloads and depends on Project Borealis for selected application integration capabilities. Delta supports workflows for Atlas Logistics, a Nexus customer. Security Engineering coordinates access reviews and deployment controls for the project. The project team uses standardized container policies and reviews changes before production rollout. The document does not provide a cloud provider name or employee compensation details. Maria Lopez is the primary engineering contact mentioned for the Delta workstream."},
    {"document_id":"DOC-010","title":"Security Engineering Organization Report","metadata":{"department":"Security Engineering","year":2026},"content":
     "Security Engineering is a department of Nexus Corporation and operates from the New York Operations Center, also called NY Operations or the NYC Hub. Maria Lopez belongs to Security Engineering and contributes to Project Delta. The department maintains Kubernetes security controls and container-policy tooling used across Nexus services. Security Engineering reviews deployment permissions and production access for multiple projects. The report identifies the New York Operations Center as the department's primary working location. It does not state individual salaries, cloud-provider contracts, or customer pricing. The team works closely with Cloud Engineering when platform-level security changes affect Kubernetes workloads."},
    {"document_id":"DOC-011","title":"Aether Cross-Team Collaboration Notes","metadata":{"project":"Project Aether","year":2026},"content":
     "The Aether collaboration notes describe cross-team work between Cloud Engineering and Data Platforms. Priya Sharma from Data Platforms contributes to Project Aether in addition to her work on Project Borealis. Alex Mercer remains the engineering manager for Aether. The notes describe Aether as a shared platform that provides data capabilities to Borealis and other internal services. PostgreSQL remains the primary relational database and Redis is used for selected low-latency workloads. The document does not define employee compensation or the infrastructure vendor. The collaboration model allows engineers from different departments to contribute without changing project management ownership."},
    {"document_id":"DOC-012","title":"Cygnus Risk Product Brief","metadata":{"product":"NexusRiskEngine","year":2026},"content":
     "Project Cygnus produces NexusRiskEngine, abbreviated as NRE or called the Risk Engine by customer teams. Mercury Health uses the product for selected risk-analysis workflows. Daniel Kim manages Cygnus and coordinates the engineering roadmap. Cygnus uses Apache Kafka and PostgreSQL as core technologies. The product brief explains that event streams are transformed into analytical records before being evaluated by the risk service. Mercury Health receives product updates through the Nexus customer operations team. The brief does not disclose cloud-provider information or employee salaries."},
    {"document_id":"DOC-013","title":"Atlas Logistics Delta Integration","metadata":{"customer":"Atlas Logistics","year":2026},"content":
     "Atlas Logistics uses Project Delta, also known as Delta Shield, for selected security and integration workflows. Maria Lopez works on Delta from the Security Engineering organization. Delta depends on Project Borealis for application-facing integration capabilities. The customer deployment uses Kubernetes-based services and standardized security policies. Atlas Logistics coordinates maintenance windows with Nexus Corporation. The document does not identify a cloud provider, individual compensation, or customer contract value. The integration team treats Delta and Borealis as separate services connected through controlled interfaces."},
]

questions = [
    {"id":"Q-001","type":"1-hop","question":"Who manages Project Aether?","answer":"Alex Mercer","path":["EMP-001 MANAGES PROJ-001"],"source_documents":["DOC-001"]},
    {"id":"Q-002","type":"1-hop","question":"Which technology does Project Borealis use?","answer":"Kubernetes","path":["PROJ-002 USES TECH-002"],"source_documents":["DOC-002"]},
    {"id":"Q-003","type":"2-hop","question":"Which technology is used by the project that Alex Mercer manages?","answer":"PostgreSQL and Redis","path":["EMP-001 MANAGES PROJ-001","PROJ-001 USES TECH-001/TECH-004"],"source_documents":["DOC-001"]},
    {"id":"Q-004","type":"1-hop","question":"Which project does Project Borealis depend on?","answer":"Project Aether","path":["PROJ-002 DEPENDS_ON PROJ-001"],"source_documents":["DOC-002"]},
    {"id":"Q-005","type":"2-hop","question":"Which customer is served by the project Priya Sharma works on?","answer":"FinGlobal Inc.","path":["EMP-002 WORKS_ON PROJ-002","PROJ-002 SERVES CUST-001"],"source_documents":["DOC-002","DOC-003"]},
    {"id":"Q-006","type":"2-hop","question":"Which technology is used by the project that Project Borealis depends on?","answer":"PostgreSQL and Redis","path":["PROJ-002 DEPENDS_ON PROJ-001","PROJ-001 USES TECH-001/TECH-004"],"source_documents":["DOC-002","DOC-001"]},
    {"id":"Q-007","type":"2-hop","question":"Which employee works on the project that produces NexusDataStream?","answer":"Priya Sharma","path":["PROJ-001 PRODUCES PROD-001","EMP-002 WORKS_ON PROJ-001"],"source_documents":["DOC-004","DOC-011"]},
    {"id":"Q-008","type":"2-hop","question":"Where is the department located that Alex Mercer belongs to?","answer":"Seattle Technology Center","path":["EMP-001 BELONGS_TO DEPT-001","DEPT-001 LOCATED_IN LOC-001"],"source_documents":["DOC-004"]},
    {"id":"Q-009","type":"3-hop","question":"Which technology is used by the project that depends on the project producing NexusDataStream?","answer":"Kubernetes and FastAPI","path":["PROJ-001 PRODUCES PROD-001","PROJ-002 DEPENDS_ON PROJ-001","PROJ-002 USES TECH-002/TECH-005"],"source_documents":["DOC-004","DOC-002","DOC-008"]},
    {"id":"Q-010","type":"3-hop","question":"Who manages the project that the project serving FinGlobal depends on?","answer":"Alex Mercer","path":["PROJ-002 SERVES CUST-001","PROJ-002 DEPENDS_ON PROJ-001","EMP-001 MANAGES PROJ-001"],"source_documents":["DOC-003","DOC-002","DOC-001"]},
    {"id":"Q-011","type":"3-hop","question":"Which customer is connected to the project that depends on Project Borealis?","answer":"Atlas Logistics","path":["PROJ-004 DEPENDS_ON PROJ-002","PROJ-004 SERVES CUST-003"],"source_documents":["DOC-009","DOC-013"]},
    {"id":"Q-012","type":"2-hop","question":"Which company does the Data Platforms department belong to, and where is it located?","answer":"Nexus Corporation; Austin Engineering Office","path":["DEPT-002 BELONGS_TO COMP-001","DEPT-002 LOCATED_IN LOC-003"],"source_documents":["DOC-006"]},
    {"id":"Q-013","type":"aggregation","question":"How many technologies does Cloud Engineering maintain?","answer":"2","path":["DEPT-001 MAINTAINS TECH-001","DEPT-001 MAINTAINS TECH-002"],"source_documents":["DOC-005"]},
    {"id":"Q-014","type":"2-hop","question":"Which customer uses the product produced by Project Cygnus?","answer":"Mercury Health","path":["PROJ-003 PRODUCES PROD-002","PROD-002 USED_BY CUST-002"],"source_documents":["DOC-007","DOC-012"]},
    {"id":"Q-015","type":"3-hop","question":"Which technology is used by the project serving Mercury Health?","answer":"Apache Kafka and PostgreSQL","path":["PROJ-003 SERVES CUST-002","PROJ-003 USES TECH-003/TECH-001"],"source_documents":["DOC-007","DOC-012"]},
    {"id":"Q-016","type":"3-hop","question":"Which customer is served by the project that depends on the project serving FinGlobal?","answer":"Atlas Logistics","path":["PROJ-002 SERVES CUST-001","PROJ-004 DEPENDS_ON PROJ-002","PROJ-004 SERVES CUST-003"],"source_documents":["DOC-003","DOC-009","DOC-013"]},
    {"id":"Q-017","type":"2-hop","question":"Where does the employee who manages Project Cygnus belong, and where is that department located?","answer":"Data Platforms; Austin Engineering Office","path":["EMP-003 MANAGES PROJ-003","EMP-003 BELONGS_TO DEPT-002","DEPT-002 LOCATED_IN LOC-003"],"source_documents":["DOC-007","DOC-006"]},
    {"id":"Q-018","type":"comparison","question":"Which employee works on both Project Borealis and Project Aether?","answer":"Priya Sharma","path":["EMP-002 WORKS_ON PROJ-002","EMP-002 WORKS_ON PROJ-001"],"source_documents":["DOC-002","DOC-011"]},
    {"id":"Q-019","type":"comparison","question":"Which project depends on Borealis and also serves a customer?","answer":"Project Delta; Atlas Logistics","path":["PROJ-004 DEPENDS_ON PROJ-002","PROJ-004 SERVES CUST-003"],"source_documents":["DOC-009","DOC-013"]},
    {"id":"Q-020","type":"out-of-scope","question":"What is Alex Mercer's annual salary?","answer":"Information unavailable","path":[],"source_documents":["DOC-004","DOC-005"]},
    {"id":"Q-021","type":"out-of-scope","question":"Which cloud provider hosts Project Borealis?","answer":"Information unavailable","path":[],"source_documents":["DOC-002","DOC-008"]},
    {"id":"Q-022","type":"out-of-scope","question":"What is the contract value between Nexus Corporation and FinGlobal Inc.?","answer":"Information unavailable","path":[],"source_documents":["DOC-003"]},
    {"id":"Q-023","type":"2-hop","question":"Which department maintains Kubernetes, and which location is that department based in?","answer":"Cloud Engineering; Seattle Technology Center","path":["DEPT-001 MAINTAINS TECH-002","DEPT-001 LOCATED_IN LOC-001"],"source_documents":["DOC-005","DOC-004"]},
    {"id":"Q-024","type":"3-hop","question":"Who manages the project that produces the product used by Mercury Health?","answer":"Daniel Kim","path":["PROJ-003 PRODUCES PROD-002","PROD-002 USED_BY CUST-002","EMP-003 MANAGES PROJ-003"],"source_documents":["DOC-007","DOC-012"]},
    {"id":"Q-025","type":"3-hop","question":"Which department does the employee working on Delta belong to, and where is it located?","answer":"Security Engineering; New York Operations Center","path":["EMP-004 WORKS_ON PROJ-004","EMP-004 BELONGS_TO DEPT-003","DEPT-003 LOCATED_IN LOC-002"],"source_documents":["DOC-009","DOC-010"]},
    {"id":"Q-026","type":"2-hop","question":"Which technology is maintained by the department Daniel Kim belongs to?","answer":"Apache Kafka and PostgreSQL","path":["EMP-003 BELONGS_TO DEPT-002","DEPT-002 MAINTAINS TECH-003/TECH-001"],"source_documents":["DOC-006"]},
    {"id":"Q-027","type":"3-hop","question":"Which customer is associated with the product produced by the project managed by Daniel Kim?","answer":"Mercury Health","path":["EMP-003 MANAGES PROJ-003","PROJ-003 PRODUCES PROD-002","PROD-002 USED_BY CUST-002"],"source_documents":["DOC-007","DOC-012"]},
    {"id":"Q-028","type":"3-hop","question":"Which technology is used by the project serving Atlas Logistics?","answer":"Kubernetes","path":["PROJ-004 SERVES CUST-003","PROJ-004 USES TECH-002"],"source_documents":["DOC-009","DOC-013"]},
    {"id":"Q-029","type":"2-hop","question":"Which company employs Priya Sharma?","answer":"Nexus Corporation","path":["EMP-002 WORKS_AT COMP-001"],"source_documents":["DOC-002","DOC-006"]},
    {"id":"Q-030","type":"3-hop","question":"Which customer is served by a project that uses FastAPI and depends on Aether?","answer":"FinGlobal Inc.","path":["PROJ-002 USES TECH-005","PROJ-002 DEPENDS_ON PROJ-001","PROJ-002 SERVES CUST-001"],"source_documents":["DOC-002","DOC-003","DOC-008"]},
]

readme = """# Hybrid RAG Synthetic Enterprise Dataset

This dataset is designed for a Hybrid Knowledge Graph + Vector RAG project using:

- Neo4j Aura
- PostgreSQL + pgvector
- LangGraph
- Gemini
- FastAPI

## Files

- `documents.json` — primary ingestion corpus. Extract entities and relationships from this file.
- `entities.json` — canonical entity ground truth and aliases.
- `relationships.json` — relationship ground truth. Use this for validation/evaluation, NOT as the primary Neo4j ingestion source.
- `questions.json` — evaluation benchmark with expected answers and graph paths.

## Important ingestion rule

Do NOT simply insert `entities.json` and `relationships.json` into Neo4j.

The intended pipeline is:

documents -> chunking -> Gemini entity/relationship extraction -> entity resolution -> Neo4j

The ground-truth files are used to check whether extraction and resolution are correct.

## Corpus

28 entities
44 relationships
13 documents
30 evaluation questions

## Entity types

Company, Employee, Department, Project, Technology, Product, Customer, Location

## Relationship types

WORKS_AT, BELONGS_TO, MANAGES, WORKS_ON, USES, DEPENDS_ON, PRODUCES, USED_BY, SERVES, LOCATED_IN, MAINTAINS

## Evaluation categories

- 1-hop factual questions
- 2-hop questions
- 3-hop questions
- multi-hop questions
- comparison questions
- aggregation questions
- out-of-scope / unavailable-information questions
- alias/entity-resolution cases

## Suggested project order

1. Load and validate `documents.json`
2. Chunk documents
3. Build vector-only baseline
4. Store chunks in PostgreSQL + pgvector
5. Create Neo4j constraints/schema
6. Extract entities/relationships with Gemini
7. Resolve aliases to canonical entities
8. Insert validated graph data into Neo4j
9. Build parameterized Cypher retrieval templates
10. Add LangGraph routing
11. Merge vector + graph evidence
12. Validate citations
13. Benchmark vector-only vs hybrid RAG
"""

files = {
    "entities.json": entities,
    "relationships.json": relationships,
    "documents.json": documents,
    "questions.json": questions,
}
for name, data in files.items():
    with open(os.path.join(base, name), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

with open(os.path.join(base, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)

# Zip everything for convenient upload
import shutil
zip_path = shutil.make_archive("/mnt/data/hybrid_rag_dataset", "zip", base)
print(f"Created: {zip_path}")
print(f"Entities: {len(entities)} | Relationships: {len(relationships)} | Documents: {len(documents)} | Questions: {len(questions)}")
