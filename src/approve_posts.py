from __future__ import annotations

from content.approval_queue import approve_post, list_latest_posts


def main() -> None:
    posts = list_latest_posts()

    if not posts:
        print("No latest posts found.")
        return

    print("\nLatest generated posts:\n")
    for idx, post in enumerate(posts, start=1):
        print(f"{idx}. {post.name}")

    raw = input("\nEnter numbers to approve, comma-separated (example: 1,3,5): ").strip()
    if not raw:
        print("No posts selected.")
        return

    chosen = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            chosen.append(int(part))
        except ValueError:
            print(f"Skipping invalid entry: {part}")

    for idx in chosen:
        if 1 <= idx <= len(posts):
            approved_path = approve_post(posts[idx - 1].name)
            print(f"Approved: {approved_path}")
        else:
            print(f"Skipping out-of-range selection: {idx}")


if __name__ == "__main__":
    main()

