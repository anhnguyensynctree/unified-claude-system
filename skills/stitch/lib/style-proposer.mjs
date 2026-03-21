/**
 * Style proposer — maps extracted project signals to a concrete stitch init config proposal.
 * Returns a proposal object + a human-readable explanation of why each choice was made.
 */

export function proposeStyleConfig(signals) {
  const proposal = {};
  const reasoning = [];

  // ── Profile ───────────────────────────────────────────────────────────────
  if (signals.isMarketing) {
    proposal.profile = "marketing";
    reasoning.push("profile: marketing — detected landing page / promotional context");
  } else if (signals.isDense) {
    proposal.profile = "dense";
    reasoning.push("profile: dense — detected admin / internal tool / data-heavy context");
  } else {
    proposal.profile = "product";
    reasoning.push("profile: product — default for SaaS / consumer / B2B apps");
  }

  // ── Platform ─────────────────────────────────────────────────────────────
  if (signals.isMobile || signals.hasReactNative) {
    proposal.platform = "Mobile, Mobile-first";
    reasoning.push("platform: Mobile — detected React Native / Expo / mobile keywords");
  } else {
    proposal.platform = "Web, Desktop-first";
  }

  // ── Aesthetic anchor ──────────────────────────────────────────────────────
  if (signals.isPremium && signals.isCreative) {
    proposal.aestheticAnchor = "editorial luxury";
    reasoning.push("aesthetic: editorial luxury — premium + creative signals");
  } else if (signals.isPremium) {
    proposal.aestheticAnchor = "sophisticated minimal";
    reasoning.push("aesthetic: sophisticated minimal — premium/luxury keywords detected");
  } else if (signals.isPlayful) {
    proposal.aestheticAnchor = "vibrant friendly";
    reasoning.push("aesthetic: vibrant friendly — playful/casual keywords detected");
  } else if (signals.isTech || signals.isDense) {
    proposal.aestheticAnchor = "dark minimal";
    reasoning.push("aesthetic: dark minimal — developer/technical context detected");
  } else if (signals.isEnterprise) {
    proposal.aestheticAnchor = "modern professional";
    reasoning.push("aesthetic: modern professional — enterprise/B2B context detected");
  } else if (signals.isMarketing) {
    proposal.aestheticAnchor = "editorial";
    reasoning.push("aesthetic: editorial — marketing/promotional context");
  } else {
    proposal.aestheticAnchor = "modern minimal";
    reasoning.push("aesthetic: modern minimal — default product aesthetic");
  }

  // ── Brand reference ───────────────────────────────────────────────────────
  if (signals.brandMentions.length > 0) {
    // Use the first mentioned brand as a style reference
    const ref = signals.brandMentions[0];
    proposal.brandReference = `similar to ${capitalize(ref)}`;
    reasoning.push(`brand reference: ${ref} — mentioned in project docs`);
  } else if (signals.isTech) {
    proposal.brandReference = "similar to Linear";
    reasoning.push("brand reference: Linear — tech/developer tool default");
  } else if (signals.isMarketing) {
    proposal.brandReference = "similar to Vercel";
    reasoning.push("brand reference: Vercel — marketing/editorial default");
  } else if (signals.isEnterprise) {
    proposal.brandReference = "similar to Stripe";
    reasoning.push("brand reference: Stripe — enterprise/professional default");
  }
  // No brand reference for generic product — let aesthetic anchor carry it

  // ── Color palette ─────────────────────────────────────────────────────────
  if (signals.colorMentions.length > 0) {
    proposal.colorPalette = signals.colorMentions.slice(0, 3).join(", ");
    reasoning.push(`color palette: extracted from docs — ${proposal.colorPalette}`);
  } else if (signals.isPremium) {
    proposal.colorPalette = "near-black backgrounds, warm ivory accents, fine gold details";
    reasoning.push("color palette: premium dark — inferred from luxury/premium signals");
  } else if (signals.isPlayful) {
    proposal.colorPalette = "vibrant accent on white, bold contrast, warm tones";
    reasoning.push("color palette: vibrant — inferred from playful/casual signals");
  } else if (signals.isTech) {
    proposal.colorPalette = "deep slate background, teal or violet accent, muted neutrals";
    reasoning.push("color palette: dark tech — inferred from developer/technical signals");
  }
  // Otherwise leave palette undefined — prompt-builder uses profile defaults

  // ── Typography ────────────────────────────────────────────────────────────
  if (signals.isPremium && !signals.isTech) {
    proposal.typography = "Serif headline (Playfair Display or similar), clean sans-serif body";
    reasoning.push("typography: serif headlines — premium aesthetic signals");
  } else if (signals.isTech || signals.isDense) {
    proposal.typography = "Geist or Inter for UI, Geist Mono for code and data";
    reasoning.push("typography: Geist/mono — technical/developer context");
  }
  // Otherwise let profile default handle it

  // ── Notes ─────────────────────────────────────────────────────────────────
  const notes = [];
  if (signals.productName) {
    notes.push(`Product: ${signals.productName}`);
  }
  if (signals.headingKeywords.length > 0) {
    notes.push(`Context keywords: ${signals.headingKeywords.slice(0, 8).join(", ")}`);
  }
  if (notes.length > 0) {
    proposal.notes = notes.join(". ");
  }

  return { proposal, reasoning };
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
