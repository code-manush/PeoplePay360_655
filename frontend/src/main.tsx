import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

const themeFromQuery = new URLSearchParams(window.location.search).get('theme');
if (themeFromQuery === 'dark' || themeFromQuery === 'light') {
  localStorage.setItem('theme', themeFromQuery);
  document.documentElement.setAttribute('data-theme', themeFromQuery);
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
