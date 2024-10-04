import fs from "fs";
import { parseOpenRPCDocument } from "@open-rpc/schema-utils-js";

console.log("Loading files...\n");

let methods = [];
let methodsBase = "src/methods/";
let methodFiles = fs.readdirSync(methodsBase);
methodFiles.forEach(file => {
  console.log(file);
  let raw = fs.readFileSync(methodsBase + file);
  let parsed = JSON.parse(raw);
  methods = [
    ...methods,
    ...parsed,
  ];
});

let schemas = {};
let schemasBase = "src/schemas/"
let schemaFiles = fs.readdirSync(schemasBase);
schemaFiles.forEach(file => {
  console.log(file);
  let raw = fs.readFileSync(schemasBase + file);
  let parsed = JSON.parse(raw);
  schemas = {
    ...schemas,
    ...parsed,
  };
});


let content = {};
let contentBase = "src/content/"
let contentFiles = fs.readdirSync(contentBase);
contentFiles.forEach(file => {
  console.log(file);
  let raw = fs.readFileSync(contentBase + file);
  let parsed = JSON.parse(raw);
  content = {
    ...content,
    ...parsed,
  };
});

let errors = {};
let errorBase = "src/errors/"
let errorFiles = fs.readdirSync(errorBase)
errorFiles.forEach(file => {
  console.log(file);
  let raw = fs.readFileSync(errorBase + file);
  let parsed = JSON.parse(raw);
  errors = {
    ...errors,
    ...parsed,
  };
});

let spec = await parseOpenRPCDocument({
  openrpc: "1.2.4",
  info: {
    title: "Portal Network JSON-RPC Specification",
    description: "A specification of the standard interface for Portal Network clients.",
    license: {
      name: "CC0-1.0",
      url: "https://creativecommons.org/publicdomain/zero/1.0/legalcode"
    },
    version: "0.0.1"
  },
  methods: methods,
  components: {
    contentDescriptors: content,
    schemas: schemas,
    errors: errors
  }
},
    {dereference: false})

let data = JSON.stringify(spec, null, '\t');
fs.writeFileSync('openrpc.json', data);

console.log();
console.log("Build successful.");
