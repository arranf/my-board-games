#! /usr/bin/env node
//
// This script updates the config.json with names for games where the name is missing
//

import { BggClient } from 'boardgamegeekclient';
import {readFile, writeFile} from "node:fs/promises";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  const client = BggClient.Create();
  let config = await readFile("./config.json");
  config = JSON.parse(config);
  
  const gamesToFetch = Object.entries(config.additional).filter(([_id, properties]) => !properties.name);
  console.info(`Ids to fetch this run: ${gamesToFetch.map(([id, _]) => id).join(', ')}`)

  const chunkSize = 20
  for (let i = 0; i < gamesToFetch.length; i += chunkSize) {
      const games = gamesToFetch.slice(i, i + chunkSize);
    const responses = await client.thing.query({ id: games.map(([id, _]) => id), 
                                                         videos: 0,
                                                         comments: 0,
                                                         marketplace: 0,
                                                         stats: 0,
                                                         type: "boardgame" });

    for (const game of responses) {
      const name = parseHtmlEntities(game.name)
      console.info(`Fetched ${game.id} as ${name}`)
      config.additional[game.id.toString()].name = name
    }
    console.info('Made a request for up to 20 items. Sleeping for 2 seconds!')
    await sleep(2000);
  }

  await writeFile("./config.json", JSON.stringify(config, null, 2));
}

main();

function parseHtmlEntities(str) {
    return str.replace(/&#([0-9]{1,3});/gi, function(match, numStr) {
        var num = parseInt(numStr, 10); // read num as normal number
        return String.fromCharCode(num);
    });
}
