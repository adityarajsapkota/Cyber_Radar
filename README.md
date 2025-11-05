
# Cyber Radar 

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![status](https://img.shields.io/badge/status-active-success.svg)]()

Cyber Radar is a powerful, automated cybersecurity news aggregator. It systematically scrapes top-tier news and vulnerability feeds, stores the data, and exposes it through a clean, high-performance FastAPI endpoint, ensuring you never miss a critical update in the world of cyber threats.

---

## ✨ Key Features

*   **Multi-Source Aggregation**: Gathers news from a configurable list of leading cybersecurity sources (The Hacker News, Dark Reading, etc.).
*   **Automated Scraping**: A built-in scheduler runs every 24 hours to fetch the latest content automatically.
*   **Persistent Storage**: Saves all collected articles in a simple and portable CSV file, preventing data loss on restart and avoiding duplicates.
*   **High-Performance API**: Built with FastAPI to serve the latest news data in a fast, reliable, and well-documented JSON format.
*   **Interactive Documentation**: Comes with automatically generated and interactive API documentation (via Swagger UI & ReDoc).
*   **Easy to Configure**: Key settings like feed URLs and the scraping schedule can be easily modified through environment variables.

## 🛠️ Technology Stack

*   **Backend**: FastAPI
*   **Data Parsing**: Feedparser
*   **Data Handling**: Pandas
*   **Task Scheduling**: APScheduler
*   **API Specification**: OpenAPI, JSON Schema
*   **Server**: Uvicorn (ASGI)

## 🚀 Getting Started

Follow these instructions to get a local copy up and running for development and testing purposes.

### Prerequisites

*   Python 3.9+
*   Git

### Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/adityarajsapkota/Cyber_Radar.git
    cd Cyber_Radar
    ```

2.  **Create and Activate a Virtual Environment**

    *   **Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    *   **macOS / Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

Once the setup is complete, you can start the application with a single command:

```bash
python run.py
```

The server will be live at `http://127.0.0.1:8000`.

Upon starting, the application will perform an initial scrape of the news feeds.

2. Launch the Streamlit Dashboard
In a new terminal, launch the Streamlit dashboard.
code
Bash
```streamlit run dashboard.py```

The dashboard will be accessible at `http://localhost:8501`.

The API provides endpoints to access the aggregated news data.

### Interactive API Documentation

The best way to explore the API is through the interactive documentation. Once the server is running, navigate to:

*   **Swagger UI**: `http://127.0.0.1:8000/docs`

Here you can view all available endpoints, see their request/response models, and even execute API calls directly from your browser.


## 📂 Project Structure

Cyber_Radar/
├── app/ # Core application source code
│ ├── api.py # API endpoint definitions
│ ├── config.py # Application configuration settings
│ ├── main.py # FastAPI application entry point
│ ├── models.py # Pydantic data models
│ ├── scraper.py # News scraping logic
│ ├── scheduler.py # Background task scheduling
│ └── storage.py # Data storage and retrieval (CSV)
├── data/ # Directory for the output CSV file
│ └── cybersecurity_news.csv
├── dashboard.py # The Streamlit dashboard script
├── requirements.txt # Project dependencies
└── README.md # This file


## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request



