import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Input, Button, Logo } from "../components/ui";
import { api, type ApiError } from "../lib/api";
import styles from "./Auth.module.css";

export function RegisterPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setIsLoading(true);

    try {
      await api.register({ email, password });
      navigate("/login", { state: { registered: true } });
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || "Failed to create account");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <Logo />

      <div className={styles.card}>
        <div className={styles.header}>
          <h1 className={styles.title}>Create your account</h1>
          <p className={styles.subtitle}>
            Start curating your personalized news feed
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
              placeholder="Min. 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>

          <Button type="submit" fullWidth isLoading={isLoading}>
            Create Account
          </Button>

          <p className={styles.terms}>
            By signing up, you agree to our{" "}
            <Link to="/terms">Terms of Service</Link> and{" "}
            <Link to="/privacy">Privacy Policy</Link>
          </p>
        </form>
      </div>

      <div className={styles.footer}>
        <span className={styles.footerText}>Already have an account?</span>
        <Link to="/login">Sign in</Link>
      </div>
    </div>
  );
}
