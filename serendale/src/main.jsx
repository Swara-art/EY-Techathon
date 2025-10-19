import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import GetStarted from './pages/GetStarted.jsx'
import Dashboard from './pages/dashboard.jsx';


const router = createBrowserRouter([
  { path: '/', element: <App /> },
  { path: '/get-started', element: <GetStarted /> },
  { path: '/dashboard', element: <Dashboard /> },
])

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
