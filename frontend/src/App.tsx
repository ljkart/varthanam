import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./components/AuthProvider";
import { ProtectedRoute } from "./components/ProtectedRoute";
import {
  LoginPage,
  RegisterPage,
  HomePage,
  CollectionsPage,
  FeedsPage,
  DashboardPage,
  ArticleReaderPage,
  RulesPage,
} from "./pages";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/app"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/app/collections"
            element={
              <ProtectedRoute>
                <CollectionsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/app/feeds"
            element={
              <ProtectedRoute>
                <FeedsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/app/articles/:articleId"
            element={
              <ProtectedRoute>
                <ArticleReaderPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/app/rules"
            element={
              <ProtectedRoute>
                <RulesPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
