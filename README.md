# Global Superstore OLAP Analytics

An interactive data analytics project focused on identifying profit inefficiencies and uncovering hidden product opportunities in retail transactions using OLAP-based analysis.

The project explores sales, discount, product profitability, and regional performance through three analytical modules, supported by a Streamlit application and a relational and document-based data architecture.

## Project Background

High sales volume does not necessarily translate into optimal profitability. Excessive discounts, loss-making products, and regional cost inefficiencies can reduce business performance even when transaction volumes are high.

At the same time, products with low purchase frequency but high profit potential may remain overlooked.

This project aims to transform retail transaction data into actionable analytical insights to support more sustainable, profit-oriented business decisions.

## Project Objectives

### 1. Trap Product & Cross-Selling Analysis

Identify high-volume products with negative profit margins and explore cross-selling patterns to investigate potential product bundling opportunities.
The objective is to understand whether complementary products can improve overall transaction profitability.

### 2. Discount Dependency Analysis

Examine the relationship between discount levels and profit-margin erosion to identify potential discount thresholds and support more informed promotional decisions.

### 3. Hidden High Value

Identify products characterized by relatively low purchase frequency and high profit, then explore their distribution across regions to uncover potential local market opportunities.

## Dataset

**Source:** [Global Superstore Dataset — Kaggle](https://www.kaggle.com/datasets/apoorvaappz/global-super-store-dataset)

The project uses retail transaction data containing customer, product, location, order, sales, discount, profit, and shipping information.

Detailed dataset statistics, including the number of records, attributes, missing values, duplicate records, and transaction period, will be documented after the source data is profiled.

## Data Architecture

The proposed data architecture combines relational and document-oriented storage.

### MySQL

The relational schema separates transactional facts from descriptive dimensions.

| Table          | Purpose                                                                         |
| -------------- | ------------------------------------------------------------------------------- |
| `dim_customer` | Customer identifiers, names, and segments                                       |
| `dim_product`  | Product identifiers, names, categories, and subcategories                       |
| `dim_location` | Geographic and market attributes                                                |
| `fact_sales`   | Transaction measures, order dates, product references, and shipping information |

### MongoDB

The `product_catalog` collection is intended to store product catalog information, including product identifiers, names, categories, subcategories, and additional attributes.

The final collection structure will be documented after the implementation is verified.

## Analytical Approach

The analysis focuses on three areas:

* **Product profitability:** examine sales, profit, quantity, and purchase frequency.
* **Discount efficiency:** compare discount levels with profitability indicators.
* **Regional opportunity:** use regional filters to explore the distribution of high-value, low-frequency products.

The exact metrics, aggregation logic, and OLAP operations will be documented according to the final implementation.

## Application

The project includes a Streamlit interface for presenting analytical results.

Application screenshots and a usage walkthrough will be added once the interface and analysis modules are finalized.

### Technology Stack

* **Programming Language:** Python
* **Web Application Framework:** Streamlit
* **Data Visualization:** Plotly
* **Relational Database:** MySQL
* **NoSQL Database:** MongoDB

## Contributors

* **Yunita Wijaya** — Hidden-High Value Segmentation
* **Jericho Sundjaja** — Discount Dependency Analysis
* **Kenneth Sujayaputera** — Trap Product & Cross-Selling Analysis

Contributor names and descriptions should be finalized with the project team.

## Project Status

Developed as a university course project. The repository is being consolidated and documented for portfolio presentation.

Some implementation details and analytical modules may require further verification before the application can be reproduced end to end.
