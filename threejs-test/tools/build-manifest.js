import { readdirSync, writeFileSync } from "fs";
import { join } from "path";

const assetsDir = join(process.cwd(), "threejs-test", "assets");
const files = readdirSync(assetsDir)
  .filter((name) => name.toLowerCase().endsWith(".glb"))
  .filter((name) => {
    const lower = name.toLowerCase();
    if (lower.startsWith("car_")) {
      return lower.startsWith("car_sedan_") || lower.startsWith("car_truck_");
    }
    return true;
  })
  .sort();

const manifest = {
  generatedAt: new Date().toISOString(),
  assets: files.map((name) => `./${name}`)
};

writeFileSync(join(assetsDir, "manifest.json"), JSON.stringify(manifest, null, 2));

console.log(`Wrote manifest.json with ${files.length} assets.`);
