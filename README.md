
# AI Meal Planner

**Fine-tuned TinyLlama-1.1B model on AWS Trainium for personalized meal planning and recipe generation.**

The AI Meal Planner transforms natural language meal requests into structured recipes with ingredients, calorie counts, and shopping links to Amazon Fresh.

---

## Project Overview

The AI Meal Planner acts as a conversational assistant that:

* Suggests meal plans based on dietary constraints and ingredients.
* Generates structured recipes with calorie estimates.
* Provides direct shopping links for each ingredient via Amazon Fresh.

**Example Query:**
“I have chicken and broccoli — under 500 calories, high protein.”

**Example Output:**
A formatted recipe with title, ingredients, cooking steps, and total calories.

---

## Model

**Base Model:** TinyLlama/TinyLlama-1.1B-Chat-v1.0
**Fine-Tuning Domain:** Meal planning, calorie estimation, and recipe generation
**Dataset Size:** 20,000 conversational samples in JSON format

Each data point follows a structured format of system, user, and assistant messages — enabling the model to learn context-aware response generation.

**Why a Small Language Model (SLM)?**

* Lightweight (1.1B parameters) → ideal for hackathon constraints
* Fast inference and low latency on AWS Trainium
* Produces structured, low-hallucination responses for domain-specific queries

---

## Training Infrastructure

| Component             | Technology                                             |
| --------------------- | ------------------------------------------------------ |
| **Training Instance** | AWS SageMaker `ml.trn1.2xlarge` (Trainium)             |
| **Frameworks**        | Hugging Face Transformers, Optimum Neuron, PEFT (LoRA) |
| **Precision**         | BF16                                                   |
| **Parallelism**       | Tensor Parallel = 2                                    |
| **Storage**           | Amazon S3 Buckets                                      |
| **Logging**           | CloudWatch Logs                                        |

**Training Pipeline:**
S3 Dataset → SageMaker Training Job on Trainium → LoRA Adapter Checkpoints → Adapter Merge → Deployed Model on SageMaker Endpoint

---

**Key Observations:**

* The fine-tuned TinyLlama produced coherent recipes with consistent calorie formatting.
* Responses adhered to dietary constraints with strong generalization to unseen queries.

---

## Deployment

| Layer           | Details                                                                            |
| --------------- | ---------------------------------------------------------------------------------- |
| **Endpoint**    | SageMaker Inference Endpoint (`tinyllama-finetuned-model-2025-11-08-23-45-51-077`) |
| **Backend**     | FastAPI service wrapping SageMaker Predictor                                       |
| **Frontend**    | Static HTML, CSS, and JavaScript                                                   |
| **Integration** | IngredientMapper for Amazon Fresh product links                                    |
| **APIs**        | `/plan`, `/recipe`, `/ingredients/shop`, `/health`                                 |

**Architecture Summary:**
User Query → FastAPI → SageMaker Endpoint → Model Inference → Ingredient Mapper → Response with Shopping Links

---

## Application Features

**Backend (FastAPI):**

* Connects to SageMaker inference endpoint
* Extracts ingredient lists from model output
* Generates Amazon Fresh shopping URLs dynamically

**Frontend (HTML + JS):**

* Chat-style interface with example prompts
* Loading animation during model generation
* Real-time recipe display with clickable ingredient links

**Key Endpoints:**

* `/plan`: Generate meal plan from natural language query
* `/recipe`: Generate recipe from listed ingredients
* `/ingredients/shop`: Get Amazon Fresh URLs
* `/health`: Service readiness and endpoint verification

---

## Tech Stack

| Layer            | Technology                   |
| ---------------- | ---------------------------- |
| **Model**        | TinyLlama-1.1B-Chat          |
| **Fine-tuning**  | Hugging Face + LoRA (PEFT)   |
| **Compute**      | AWS SageMaker + Trainium     |
| **Serving**      | SageMaker Real-time Endpoint |
| **Backend**      | FastAPI                      |
| **Frontend**     | HTML, CSS, Vanilla JS        |
| **Data Storage** | Amazon S3                    |
| **Monitoring**   | AWS CloudWatch               |

---

## Key Results

* **Training Duration:** ~50 minutes
* **Data:** 20K samples (recipes, constraints, dietary preferences)
* **Endpoint Latency:** ~1.5 seconds (average for small inputs)
* **Output Quality:** Human-like recipe generation with structured formatting

---

## Future Enhancements

* Integrate BLEU / Rouge evaluation for quantitative benchmarking
* Expand dataset to 100K+ examples with regional cuisines
* Add multimodal capability (image-to-meal generation)
* Migrate backend to AWS ECS / Fargate
* Deploy frontend on Vercel for production

---

## Contributors
* Mihika Sanghvi
* Jasna Budhathoki

---
