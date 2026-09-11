/**
 * VERIFAI Forensic Headlines Data Module
 * 20 witty, cynical, and engaging copy pairs for the dynamic hero section.
 */

const VERIFAI_HEADLINES = [
  {
    headline: "Is that photo real, or did someone get creative?",
    subtext: "Upload it and we'll tell you the truth — no judgment, mostly."
  },
  {
    headline: "Real photo, or Photoshop's finest work?",
    subtext: "Drop it below. We've seen every trick in the book."
  },
  {
    headline: "Totally real. Definitely not edited. Sure.",
    subtext: "Upload your file and let's actually find out."
  },
  {
    headline: "Trust issues? Same.",
    subtext: "Instant photo and document authenticity checks — receipts included."
  },
  {
    headline: "Nice photo. Suspiciously nice.",
    subtext: "Upload it and we'll see what Photoshop left behind."
  },
  {
    headline: "We regret to inform you that pixels don't lie. Usually.",
    subtext: "Upload your evidence and let the forensics do the talking."
  },
  {
    headline: "That document has been through some things.",
    subtext: "Upload it. We'll figure out what."
  },
  {
    headline: "Every file has a story. Some are lying.",
    subtext: "Drop your photo or document and let's hear the truth."
  },
  {
    headline: "Caught editing red-handed since day one.",
    subtext: "Upload a file — we don't do vibes, we do evidence."
  },
  {
    headline: "Yes, even AI can tell when AI (or Photoshop) touched this.",
    subtext: "Upload your file for the real verdict."
  },
  {
    headline: "This file swears it's innocent.",
    subtext: "Upload it — we don't take its word for it."
  },
  {
    headline: "AI-generated? Photoshopped? Or just... normal?",
    subtext: "There's one way to find out."
  },
  {
    headline: "We've seen a thousand 'totally real' screenshots.",
    subtext: "This one's about to get the treatment too."
  },
  {
    headline: "Innocent until proven Photoshopped.",
    subtext: "Upload your file and let's see where it stands."
  },
  {
    headline: "Some files lie better than others.",
    subtext: "Let's see how good this one is."
  },
  {
    headline: "Looks legit. So did the last one.",
    subtext: "Upload it and let's not assume anything."
  },
  {
    headline: "Your file, under oath.",
    subtext: "Upload a photo or document and let it testify."
  },
  {
    headline: "Not all edits leave fingerprints. We check anyway.",
    subtext: "Upload your file for the full workup."
  },
  {
    headline: "This could be real. Or it could be someone's Tuesday project.",
    subtext: "Let's find out which."
  },
  {
    headline: "Skeptical by design. Accurate by necessity.",
    subtext: "Upload your file and let the evidence speak."
  }
];

let lastHeadlineIndex = -1;

function getRandomHeadline() {
  if (VERIFAI_HEADLINES.length === 0) return null;
  let newIndex;
  do {
    newIndex = Math.floor(Math.random() * VERIFAI_HEADLINES.length);
  } while (newIndex === lastHeadlineIndex && VERIFAI_HEADLINES.length > 1);
  lastHeadlineIndex = newIndex;
  return VERIFAI_HEADLINES[newIndex];
}

// Attach to window for browser script tag usage, or export for ES modules
if (typeof window !== "undefined") {
  window.VERIFAI_HEADLINES = VERIFAI_HEADLINES;
  window.getRandomHeadline = getRandomHeadline;
}
if (typeof module !== "undefined" && module.exports) {
  module.exports = { VERIFAI_HEADLINES, getRandomHeadline };
}
