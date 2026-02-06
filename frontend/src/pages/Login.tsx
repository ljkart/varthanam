import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Input, Button, Logo } from "../components/ui";
import { api, type ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";
import styles from "./Auth.module.css";

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const response = await api.login({ email, password });
      login(response.access_token);
      navigate("/app");
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || "Invalid email or password");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <Logo />

      <div className={styles.card}>
        <div className={styles.header}>
          <h1 className={styles.title}>Welcome back</h1>
          <p className={styles.subtitle}>
            Sign in to your account to continue reading
          </p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          {error && <div className={styles.error}>{error}</div>}

          <div className={styles.fields}>
            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />

            <div className={styles.optionsRow}>
              <label className={styles.rememberLabel}>
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className={styles.checkbox}
                />
                <span>Remember me</span>
              </label>
              <Link to="/forgot-password" className={styles.forgotLink}>
                Forgot password?
              </Link>
            </div>
          </div>

          <Button type="submit" fullWidth isLoading={isLoading}>
            Sign In
          </Button>

          <div className={styles.divider}>
            <span className={styles.dividerLine} />
            <span className={styles.dividerText}>or</span>
            <span className={styles.dividerLine} />
          </div>

          <Button
            type="button"
            variant="secondary"
            fullWidth
            leftIcon={<GoogleIcon />}
          >
            Continue with Google
          </Button>
        </form>
      </div>

      <div className={styles.footer}>
        <span className={styles.footerText}>Don't have an account?</span>
        <Link to="/register">Sign up</Link>
      </div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <circle cx="12" cy="12" r="10" />
    </svg>
  );
}
