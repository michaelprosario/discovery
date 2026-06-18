import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Spinner } from './components/Spinner';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { NotebookListPage } from './pages/NotebookListPage';
import { NewNotebookPage } from './pages/NewNotebookPage';
import { NotebookDetailPage } from './pages/NotebookDetailPage';
import { SourceViewPage } from './pages/SourceViewPage';
import { NewBlogPostPage } from './pages/NewBlogPostPage';
import { ViewOutputPage } from './pages/ViewOutputPage';
import { ChatPage } from './pages/ChatPage';
import { ArticleSearchPage } from './pages/ArticleSearchPage';

/** Public routes redirect to the app when already signed in. */
function PublicOnly({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <Spinner />;
  if (isAuthenticated) return <Navigate to="/notebooks" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicOnly>
            <LoginPage />
          </PublicOnly>
        }
      />
      <Route
        path="/register"
        element={
          <PublicOnly>
            <RegisterPage />
          </PublicOnly>
        }
      />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/notebooks" element={<NotebookListPage />} />
        <Route path="/notebooks/new" element={<NewNotebookPage />} />
        <Route path="/notebooks/:id" element={<NotebookDetailPage />} />
        <Route path="/notebooks/:id/sources/:sourceId" element={<SourceViewPage />} />
        <Route path="/notebooks/:id/new-blog-post" element={<NewBlogPostPage />} />
        <Route path="/notebooks/:id/outputs/:outputId" element={<ViewOutputPage />} />
        <Route path="/notebooks/:id/chat" element={<ChatPage />} />
        <Route path="/article-search" element={<ArticleSearchPage />} />
      </Route>

      <Route path="/" element={<Navigate to="/notebooks" replace />} />
      <Route path="*" element={<Navigate to="/notebooks" replace />} />
    </Routes>
  );
}
