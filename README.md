# A1.2 contextual search

# AI-powered-contextual-search-platform
 # Overview

This project implements a production-oriented AI-powered contextual search system for a product catalog.
It goes beyond traditional keyword search by combining:

Semantic understanding of natural-language queries

Structured filtering (price, category, rating, attributes)

Continuous learning from real user behavior

Explainable AI-assisted search results

The system is designed to resemble real-world e-commerce search architectures, with clear separation of concerns, asynchronous event processing, and deterministic ranking logic augmented by AI.

This project was built to demonstrate backend engineering, data pipeline design, system architecture, and responsible AI integration.


# Key Capabilities

- Natural language search (semantic, not keyword-based)

- Vector similarity retrieval with structured filters

- Asynchronous user behavior tracking

- Learning-based ranking improvement over time


# High-Level Architecture

Client
  ↓
API Layer (FastAPI)
  ↓
Search Service ──→ Vector Database
  ↓                   ↓
Ranking Service ←─ Behavior Signals
  ↓
Search Results + AI Explanation

Event API → Message Queue → Analytics Consumers → Stats Store


# Core design principle:
Retrieval, ranking, learning, and AI reasoning are explicitly decoupled to allow evolution and explainability.

# Product Ingestion Pipeline

The ingestion pipeline is implemented as a reusable backend service, not a one-time script.

# Supported Inputs

- CSV

- JSON

Ingestion Flow

1. Input validation and normalization

2. AI-assisted attribute extraction from descriptions

3. Semantic embedding generation

4. Dual storage:

- PostgreSQL for structured product data

- Vector database for semantic retrieval

# Embedded Text Fields

- Product title

- Description

- Category

- Extracted attributes

This ensures both semantic relevance and accurate structured filtering.


# Contextual Search Flow
The system supports queries such as:

- “Running shoes for flat feet under ₹5000”

- “Lightweight laptop for coding and gaming”

Search Execution Steps

1. AI-assisted query understanding

-  Query expansion

-  Filter extraction (price, category, attributes)

2. Query embedding generation

3. Vector similarity search (Top-K retrieval)

4. Structured filtering

5. Learning-based ranking

6. AI-generated explanation

Retrieval and ranking are handled by separate services to avoid coupling and to enable learning-based improvements.


Learning From User Behavior

User interactions are tracked asynchronously, including:

- Search queries

- Product clicks

- Add-to-cart events

- Purchases

- Dwell time
  
# Event Pipeline

- Events are captured asynchronously

- Passed through a message queue

- Processed by analytics consumers

- Aggregated into query-product statistics


 # Learning Logic (Heuristic-Based)

- Ranking improves over time using real usage data:

- Products with higher CTR and conversion rates are boosted

- Products with high bounce rates are penalized

- Dwell time contributes positively to ranking

This approach is intentionally simple, explainable, and production-friendly, while clearly demonstrating learning from behavior.

# AI Integration Strategy

AI is used to assist system reasoning, not to replace deterministic logic.

# Implemented AI features:

Query expansion and intent clarification

Automatic attribute extraction from product descriptions

AI-generated explanations for search results

# Example Explanation

“This product was shown because it matches the query intent, falls within the selected price range, and has strong historical engagement for similar searches.”

Ranking decisions remain transparent and controllable.

# Asynchronous Event Processing

To ensure scalability and low latency:

- Search APIs are never blocked by logging

- All behavioral data flows through a message queue

- Analytics and learning are fully decoupled from request handling

- This mirrors architectures used in real large-scale search systems.


# Observability

The system includes basic observability features:

- Structured logging

- Query latency tracking

- Event throughput monitoring

- Ingestion error reporting

These provide visibility into system performance and failure modes

# Technology Stack

- Backend: FastAPI (Python)

- Structured Database: PostgreSQL

- Vector Database: Weaviate / Pinecone

- Message Queue: Kafka / RabbitMQ

- AI Models: OpenAI / SentenceTransformers

- Analytics Storage: PostgreSQL (aggregated statistics)
  

api/            # HTTP APIs (search, ingestion, events)
services/       # Business logic (search, ranking, AI, ingestion)
db/             # Database models and repositories
vector_store/   # Vector database integration
analytics/      # Event consumers and aggregations
config/         # Configuration and logging

Each layer is intentionally isolated to improve maintainability and testability.

# Limitations & Future Improvements

- Personalized ranking per user

- Offline batch re-ranking jobs

- Multi-language search support

- Advanced ML-based ranking models

- Query analytics dashboard

# Why This Project Matters

This system demonstrates:

- How modern search systems are actually built

- Responsible use of AI in backend systems

- Scalable, production-ready architecture decisions

- Clear reasoning over blind model usage

It is intentionally designed to favor clarity, correctness, and explainability over complexity.

# Author
Piyush Gautam
Backend / Systems Devloper
AI-assisted Search & Data Systems
