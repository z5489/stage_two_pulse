# Antigravity Dashboard

A high-performance React dashboard for visualizing Minervini Trend Template stock scans.

## Getting Started

### 1. Prerequisites
Ensure you have the following installed:
- [Node.js](https://nodejs.org/) (v18+)
- [npm](https://www.npmjs.com/)

### 2. Installation
Navigate to this directory and install dependencies:
```bash
npm install
```

### 3. Development
Run the development server:
```bash
npm run dev
```
The dashboard will be available at `http://localhost:5173`.

## Architecture
- **Framework**: React 19 + Vite
- **Styling**: Vanilla CSS (Modern design system)
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **API**: Connects to the Python Flask server at `http://127.0.0.1:5000`

## Features
- Real-time scanning progress visualization.
- Incremental data loading (results appear as they are scanned).
- CSV/Excel export and import support.
- Interactive stock table with Minervini scoring breakdown.
