# VIB Credit Card Text Classifier

Streamlit app for automatic classification and labeling of VIB credit card data.

## Features

- Upload Excel files (.xlsx, .xls)
- Automatically merge Title, Content, Description columns
- Classify and assign 4 labels:
  - **Labels1**: CREDIT CARD (if text is related to cards)
  - **Labels2**: Specific card type (Financial Free, Cash Back, LazCard, etc.)
  - **Labels3**: Topic (Fee/Interest, Card Feature, Acquisition, etc.)
  - **Labels4**: Details (Annual fee, Card design, etc.)
- Download result file with labels filled in

## Installation

### Option 1: Local Installation

```bash
# Install required libraries
pip install -r requirements.txt
```

### Option 2: Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t vib-classifier .
docker run -p 8501:8501 vib-classifier
```

## Running the Application

### Local

```bash
streamlit run app.py
```

### Docker

```bash
docker-compose up
```

App will be available at: http://localhost:8501

## Input Excel File Structure

Excel file should contain at least one of these columns:
- `Title`: Title
- `Content`: Content
- `Description`: Description

## Output Excel File Structure

Result file will include:
- All original columns
- `merged_text`: Merged text from Title, Content, Description
- `Labels1`: Level 1 label (CREDIT CARD)
- `Labels2`: Level 2 label (Card type)
- `Labels3`: Level 3 label (Topic)
- `Labels4`: Level 4 label (Details)

## Docker Commands

```bash
# Build image
docker build -t vib-classifier .

# Run container
docker run -p 8501:8501 vib-classifier

# Using docker-compose
docker-compose up -d        # Start in background
docker-compose down         # Stop
docker-compose logs -f      # View logs
docker-compose restart      # Restart
```

## Example

**Input:**
| Title | Content | Description |
|-------|---------|-------------|
| VIB Card | I want to apply for Financial Free card | Annual fee is too high |

**Output:**
| Title | Content | Description | merged_text | Labels1 | Labels2 | Labels3 | Labels4 |
|-------|---------|-------------|-------------|---------|---------|---------|---------|
| VIB Card | I want to apply for Financial Free card | Annual fee is too high | VIB Card I want to apply for Financial Free card Annual fee is too high | THẺ TÍN DỤNG | Financial Free | Fee/Interest | Phí thường niên |
