# ETL Pipeline Documentation

## Overview
The ETL (Extract, Transform, Load) pipeline is responsible for gathering course data from various online learning platforms, processing it, and loading it into Snowflake for use by the SkillPathAI application.

## Directory Structure
```
etl/
├── extract/          # Data extraction modules
│   ├── web_scraper/  # Web scraping utilities
│   ├── fetch_kaggle_dataset.py  # Kaggle dataset downloader
│   ├── load_json_snowflake.py   # JSON data loader
│   └── process_data.py          # Data processing utilities
│
├── transform/        # Data transformation modules
│   └── dbt_transformation/  # dbt models and transformations
│
├── load/            # Data loading modules
│   └── load_to_snowflake.py  # Snowflake data loader
│
├── Cortex_Queries/  # Snowflake Cortex queries
└── main.py         # ETL orchestration script
```

## Data Sources
The pipeline extracts data from the following platforms:
- Udemy
- Coursera
- edX
- Udacity
- Pluralsight

## Pipeline Components

### 1. Extract
The extraction phase handles data collection from various sources:

#### Kaggle Datasets
- Uses `fetch_kaggle_dataset.py` to download course data from Kaggle
- Supports multiple platforms (Udemy, Coursera, edX, Udacity, Pluralsight)
- Downloads and compresses data for efficient transfer

#### Web Scraping
- Located in `extract/web_scraper/`
- Handles direct data collection from platform websites
- Implements rate limiting and error handling

### 2. Transform
The transformation phase processes the raw data:

#### dbt Transformations
- Located in `transform/dbt_transformation/`
- Uses dbt (data build tool) for SQL-based transformations
- Creates standardized schemas across platforms
- Handles data cleaning and normalization

### 3. Load
The loading phase manages data ingestion into Snowflake:

#### Snowflake Integration
- Uses `load_to_snowflake.py` for data loading
- Implements staging tables for temporary storage
- Handles incremental updates
- Manages data compression and optimization

## Usage

### Prerequisites
- Python 3.9+
- Kaggle API credentials
- Snowflake account and credentials
- dbt (for transformations)

### Environment Setup
1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure Kaggle credentials:
   ```bash
   export KAGGLE_USERNAME=your_username
   export KAGGLE_KEY=your_key
   ```

3. Configure Snowflake credentials:
   ```bash
   export SNOWFLAKE_ACCOUNT=your_account
   export SNOWFLAKE_USER=your_user
   export SNOWFLAKE_PASSWORD=your_password
   export SNOWFLAKE_WAREHOUSE=your_warehouse
   export SNOWFLAKE_DATABASE=your_database
   export SNOWFLAKE_SCHEMA=your_schema
   ```

### Running the Pipeline
1. Navigate to the etl directory:
   ```bash
   cd etl
   ```

2. Run the main ETL script:
   ```bash
   python main.py
   ```

The script will:
- Download datasets from Kaggle
- Process and transform the data
- Load the data into Snowflake
- Create necessary staging tables
- Apply dbt transformations

## Data Flow
1. Raw data is extracted from Kaggle datasets
2. Data is processed and cleaned
3. Processed data is loaded into Snowflake staging tables
4. dbt transformations are applied to create final tables
5. Data is made available for the SkillPathAI application

## Error Handling
- The pipeline includes comprehensive error handling
- Failed operations are logged with detailed error messages
- Retry mechanisms for transient failures
- Data validation at each stage

## Monitoring
- Log files are generated in the `logs/` directory
- Progress tracking for each dataset
- Error reporting and notification system

## Maintenance
- Regular updates to handle schema changes
- Monitoring of data quality
- Performance optimization
- Documentation updates

## Troubleshooting
Common issues and solutions:
1. Kaggle API errors
   - Verify API credentials
   - Check internet connectivity
   - Ensure dataset access permissions

2. Snowflake connection issues
   - Verify Snowflake credentials
   - Check network connectivity
   - Verify warehouse availability

3. Data transformation errors
   - Check dbt model configurations
   - Verify data formats
   - Review error logs

## Contributing
1. Follow the existing directory structure
2. Document new features and changes
3. Update this documentation as needed
4. Test changes before committing

## Contact
For ETL pipeline related queries, contact the development team. 