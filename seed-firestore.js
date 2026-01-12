// seed-firestore.js
// Node + Firebase Admin - carga firestore-seed.json a Firestore
const fs = require("fs");
const admin = require("firebase-admin");

const SERVICE_PATH = __dirname + "\\serviceAccountKey.json"; // pon aquí tu archivo de service account
if (!fs.existsSync(SERVICE_PATH)) {
  console.error("ERROR: No encontré serviceAccountKey.json en:\n", SERVICE_PATH);
  process.exit(1);
}

admin.initializeApp({
  credential: admin.credential.cert(require(SERVICE_PATH))
});

const db = admin.firestore();

async function upload() {
  try {
    const raw = fs.readFileSync("firestore-seed.json", "utf8");
    const data = JSON.parse(raw);

    for (const [collectionName, docs] of Object.entries(data)) {
      const colRef = db.collection(collectionName);
      console.log("Subiendo colección:", collectionName);
      for (const [docId, docData] of Object.entries(docs)) {
        await colRef.doc(docId).set(docData);
        console.log("  →", collectionName, "/", docId);
      }
    }

    console.log("✅ Carga completada.");
    process.exit(0);
  } catch (err) {
    console.error("ERROR durante la carga:", err);
    process.exit(1);
  }
}

upload();