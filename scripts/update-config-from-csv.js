#! /usr/bin/env node
//
// This script updates the config.json to include ranks from https://rankingengine.pubmeeple.com/
//

import csv from "csv-parser";
import fs from "fs";
import axios from "axios";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  let config = JSON.parse(fs.readFileSync("./config.json"));

  let titleToIdCacheContents;
  try {
    titleToIdCacheContents = fs.readFileSync("./title-cache.json");
  } catch (e) {
    // empty catch if file doesn't exist
  }

  const titleToIdCache = titleToIdCacheContents
    ? JSON.parse(titleToIdCacheContents)
    : {};

  let data = [];
  await new Promise((fulfill) =>
    fs
      .createReadStream("./rank.csv")
      .pipe(csv())
      .on("data", async (row) => {
        data.push(row);
      })
      .on("end", fulfill)
  );
  console.log(JSON.stringify(data));
  for (const item of data) {
    const name = item.Item;
    let id;
    if (titleToIdCache[name]) {
      id = titleToIdCache[name];
    } else {
      const url = `https://boardgamegeek.com/search/boardgame?q=${encodeURIComponent(
        name
      )}&nosession=1&showcount=20`;
      const { data } = await axios.get(url);
      if (data.items.length === 0) {
        console.log(`Tried to fetch ${JSON.stringify(item)}`);
        console.log(`Could not find game for ${name}`);
        process.exit(1);
      }
      const gameId = data.items[0].id;
      console.log(`Requesting ${item.Item}`);
      const idString = gameId.toString();
      titleToIdCache[name] = idString;
      id = idString;
      console.log("Sleeping...");
      await sleep(2000);
    }

    const configItem = config.additional[id];

    if (configItem) {
      config.additional[id] = {
        ...configItem,
        name,
        rank: item.Rank,
      };
    }
  }

  fs.writeFileSync("./config.json", JSON.stringify(config, null, 2));

  fs.writeFileSync("./title-cache.json", JSON.stringify(titleToIdCache));
}

main();
