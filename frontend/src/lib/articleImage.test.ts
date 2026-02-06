import { describe, it, expect } from "vitest";
import {
  extractImageFromHtml,
  getPlaceholderGradient,
  getPlaceholderLabel,
} from "./articleImage";

describe("getPlaceholderGradient", () => {
  it("returns a CSS gradient string", () => {
    const result = getPlaceholderGradient(1);
    expect(result).toMatch(/^linear-gradient/);
  });

  it("is deterministic for the same feed_id", () => {
    const a = getPlaceholderGradient(5);
    const b = getPlaceholderGradient(5);
    expect(a).toBe(b);
  });

  it("produces different gradients for different feed_ids", () => {
    const a = getPlaceholderGradient(0);
    const b = getPlaceholderGradient(1);
    expect(a).not.toBe(b);
  });

  it("cycles through gradients for large feed_ids", () => {
    const a = getPlaceholderGradient(0);
    const b = getPlaceholderGradient(8);
    expect(a).toBe(b);
  });
});

describe("getPlaceholderLabel", () => {
  it("extracts first letters of first two words", () => {
    expect(getPlaceholderLabel("Hello World")).toBe("HW");
  });

  it("handles single-word title", () => {
    expect(getPlaceholderLabel("Technology")).toBe("T");
  });

  it("handles empty title", () => {
    expect(getPlaceholderLabel("")).toBe("");
  });

  it("handles multi-word title taking only first two", () => {
    expect(getPlaceholderLabel("The Quick Brown Fox")).toBe("TQ");
  });

  it("uppercases the initials", () => {
    expect(getPlaceholderLabel("hello world")).toBe("HW");
  });
});

describe("extractImageFromHtml", () => {
  it("returns null for null input", () => {
    expect(extractImageFromHtml(null)).toBeNull();
  });

  it("returns null for empty string", () => {
    expect(extractImageFromHtml("")).toBeNull();
  });

  it("returns null for HTML without images", () => {
    expect(extractImageFromHtml("<p>No images here</p>")).toBeNull();
  });

  it("extracts img src with double quotes", () => {
    const html =
      '<p>Text</p><img src="https://example.com/image.jpg" alt="test">';
    expect(extractImageFromHtml(html)).toBe("https://example.com/image.jpg");
  });

  it("extracts img src with single quotes", () => {
    const html = "<img src='https://example.com/photo.png'>";
    expect(extractImageFromHtml(html)).toBe("https://example.com/photo.png");
  });

  it("extracts first image when multiple exist", () => {
    const html = '<img src="first.jpg"><img src="second.jpg">';
    expect(extractImageFromHtml(html)).toBe("first.jpg");
  });

  it("handles img tag with other attributes", () => {
    const html =
      '<img width="100" src="https://cdn.example.com/img.webp" height="50">';
    expect(extractImageFromHtml(html)).toBe("https://cdn.example.com/img.webp");
  });
});
