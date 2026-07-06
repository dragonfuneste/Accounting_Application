// index.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import Menuaccounts from './frontend/jsx/menu/Menuaccounts';
import './index.css'    // Tes styles

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Menuaccounts/>
    </BrowserRouter>
  </React.StrictMode>
)