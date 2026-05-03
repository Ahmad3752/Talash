# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

# Talash Frontend

This is the frontend for the Talash AI-Powered CV Processing & Candidate Evaluation Platform.

## Features
- Upload and process PDF CVs
- View and search candidate profiles
- Multi-module scoring breakdown (Education, Research, Experience, Skills, TVS/CCS)
- Email Candidate button on the Summary tab to send recommendation emails
- Real-time status, skeleton loaders, and responsive design
- Dark/Light theme toggle

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```
3. The app will be available at [http://localhost:5173](http://localhost:5173)

## Environment Variables

Create a `.env` file in this directory if you need to override Vite or API settings.

## Email Feature
- The "Email Candidate" button on the Summary tab allows you to send a recommendation email to the candidate.
- The backend must be configured with SMTP credentials for this to work.
- Button states: loading, sending, sent, error, and no-email (disabled if no email is available).

## Tech Stack
- React, Vite, TailwindCSS, Lucide React, Recharts, React Hot Toast

For backend/API and full project documentation, see the main project documentation in the root folder.
