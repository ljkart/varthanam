/**
 * Article image utilities.
 *
 * Attempts to extract images from article HTML content.
 * Falls back to deterministic placeholder gradients based on feed_id.
 */

/**
 * Attempts to extract the first image URL from HTML content.
 * Returns null if no image is found.
 */
export function extractImageFromHtml(html: string | null): string | null {
  if (!html) return null;

  // Try to find img src attribute
  const imgMatch = html.match(/<img[^>]+src=["']([^"']+)["']/i);
  if (imgMatch?.[1]) {
    return imgMatch[1];
  }

  // Try to find background-image url
  const bgMatch = html.match(/background-image:\s*url\(["']?([^"')]+)["']?\)/i);
  if (bgMatch?.[1]) {
    return bgMatch[1];
  }

  // Try to find og:image or other meta-like patterns in summary
  const ogMatch = html.match(/og:image[^>]+content=["']([^"']+)["']/i);
  if (ogMatch?.[1]) {
    return ogMatch[1];
  }

  return null;
}

const GRADIENTS: [string, string][] = [
  ["#1a1a2e", "#16213e"],
  ["#0f3460", "#1a1a2e"],
  ["#1b1b2f", "#162447"],
  ["#2d132c", "#1a1a2e"],
  ["#1a1a2e", "#0a3d62"],
  ["#1b262c", "#0f4c75"],
  ["#2c003e", "#1a1a2e"],
  ["#1a1a2e", "#1e3a5f"],
];

/**
 * Returns a deterministic CSS gradient string for an article placeholder.
 * Articles from the same feed get the same gradient.
 */
export function getPlaceholderGradient(feedId: number): string {
  const index = feedId % GRADIENTS.length;
  const [from, to] = GRADIENTS[index];
  return `linear-gradient(135deg, ${from} 0%, ${to} 100%)`;
}

/**
 * Returns 2-letter initials from an article title for overlay text.
 */
export function getPlaceholderLabel(title: string): string {
  return title
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");
}
