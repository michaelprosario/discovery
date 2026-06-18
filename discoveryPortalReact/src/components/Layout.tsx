import { NavLink, Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import styles from './Layout.module.css';

/** App chrome: top nav + the authenticated user menu. Wraps protected pages. */
export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink;

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <Link to="/notebooks" className={styles.brand}>
            🔍 Discovery
          </Link>
          <nav className={styles.nav}>
            <NavLink to="/notebooks" className={linkClass}>
              Notebooks
            </NavLink>
            <NavLink to="/article-search" className={linkClass}>
              Article Search
            </NavLink>
            <div className={styles.user}>
              <span className="muted">{user?.display_name || user?.email}</span>
              <button className="btn btn-secondary btn-sm" onClick={handleLogout}>
                Log out
              </button>
            </div>
          </nav>
        </div>
      </header>
      <main className={styles.main}>
        <div className={styles.mainInner}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
