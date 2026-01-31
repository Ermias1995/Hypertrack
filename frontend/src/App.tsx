import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ArtistsPage from './pages/ArtistsPage'
import ArtistDetailPage from './pages/ArtistDetailPage'
import Header from './components/Header'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen app-bg">
        <Header />
        <main className="relative">
          <Routes>
            <Route path="/" element={<ArtistsPage />} />
            <Route path="/artist/:id" element={<ArtistDetailPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
