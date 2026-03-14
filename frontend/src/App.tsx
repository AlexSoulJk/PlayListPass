import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './app/providers/AuthProvider'
import { AppRouter } from './app/router/AppRouter'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
