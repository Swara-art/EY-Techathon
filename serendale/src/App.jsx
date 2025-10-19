import './App.css'
import NavBar from './components/NavBar'
import Hero from './components/Hero'
import CanvasMatrix from "./components/CanvasMatrix";

export default function App() {
  return (
    <div className="bg-black text-white min-h-screen flex flex-col justify-between">
  <main className="flex-1 flex flex-col items-center justify-center text-center" style={{ position: 'relative' }}>
  
      <NavBar />
      <Hero />
      </main>
      <CanvasMatrix />
    </div>

  )
}
