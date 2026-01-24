import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ArtistsPage from './pages/ArtistsPage'
import ArtistDetailPage from './pages/ArtistDetailPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ArtistsPage />} />
        <Route path="/artist/:id" element={<ArtistDetailPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
