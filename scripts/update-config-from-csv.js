//
// This script updates the config.json to include rank from https://rankingengine.pubmeeple.com/
//

import csv from "csv-parser";
import fs from "fs";
import axios from "axios";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  let config = JSON.parse(fs.readFileSync("./config.json"));

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

  for (const item of data) {
    const url = `https://boardgamegeek.com/search/boardgame?q=${encodeURIComponent(
      item.Item
    )}&nosession=1&showcount=20`;
    const { data } = await axios.get(url);
    const id = data.items[0].id;
    console.log(`Requesting ${item.Item}`);
    const configItem = config.additional[id.toString()];

    if (configItem) {
      config.additional[id.toString()] = {
        ...configItem,
        rank: item.Rank,
      };
    }
    await sleep(2000);
  }

  fs.writeFileSync("./config.json", JSON.stringify(config));
}

main();
