// The backend has no notion of marker groups, so they live here.
// A marker goes in the first group whose pattern matches its test name;
// anything unmatched falls into OTHER_GROUP.
export interface GroupDef {
  name: string;
  patterns: RegExp[];
}

export const OTHER_GROUP = "Other";

export const GROUP_DEFS: GroupDef[] = [
  { name: "Lipid Panel", patterns: [/\bldl\b/i, /\bhdl\b/i, /trigl/i, /cholest/i, /kolest/i] },
  { name: "Blood Sugar", patterns: [/gluc/i, /gluk/i, /hba1c/i, /insulin/i] },
  { name: "Thyroid", patterns: [/\btsh\b/i, /\bf?t3\b/i, /\bf?t4\b/i, /thyro/i] },
  {
    name: "CBC",
    patterns: [
      /\brbc\b/i,
      /\bwbc\b/i,
      /h[a]?emoglobin/i,
      /h[a]?ematocrit/i,
      /platelet/i,
      /\bmcv\b/i,
      /\bmch/i,
    ],
  },
  { name: "Vitamins", patterns: [/vitamin/i, /ferritin/i, /\bb12\b/i, /folate/i] },
  { name: "Liver", patterns: [/\balt\b/i, /\bast\b/i, /\balp\b/i, /bilirubin/i, /\bggt\b/i] },
  { name: "Kidney", patterns: [/creatinin/i, /\bbun\b/i, /\begfr\b/i, /urea/i, /uric/i] },
  {
    name: "Electrolytes",
    patterns: [/sodium/i, /potassium/i, /calcium/i, /magnesium/i, /\bna\b/i, /\bk\b/i],
  },
];

export function groupFor(testName: string): string {
  const def = GROUP_DEFS.find((g) => g.patterns.some((p) => p.test(testName)));
  return def ? def.name : OTHER_GROUP;
}

// display order: defined groups first, "Other" last
export function groupOrder(name: string): number {
  const i = GROUP_DEFS.findIndex((g) => g.name === name);
  return i === -1 ? GROUP_DEFS.length : i;
}
