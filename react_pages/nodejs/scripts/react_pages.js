#!/usr/bin/env node
'use strict';

const webpack = require('webpack');
const cli = require('commander');
const ora = require('ora');
// const util = require('util');

cli
    .arguments('[settings_json]')
    .action(react_pages)
    .parse(process.argv); // end with parse to parse through the input

// Webpack output options
const normal_opts = {
  all: false,
  errors: true,
  moduleTrace: true,
  colors: true,
};
const verbose_opts = {
  colors: true,
  chunks: false,
};

function react_pages(settings_list_json) {
  const settings_list = JSON.parse(settings_list_json);

  const verbose = settings_list[0]['verbose'];
  const deploy = settings_list[0]['deploy'];

  let get_custom_config;

  if (deploy) {
    process.env.BABEL_ENV = 'production';
    process.env.NODE_ENV = 'production';
    get_custom_config = require('../config/webpack.config.prod');

  }
  else {
    process.env.BABEL_ENV = 'development';
    process.env.NODE_ENV = 'development';
    get_custom_config = require('../config/webpack.config.dev');
  }

  const spinner = ora({'spinner': 'moon'}).start();

  for (const settings of settings_list) {
    const config = get_custom_config(settings);

    // console.debug('webpack config:', util.inspect(config, false, null));
    const compiler = webpack(config);

    const handle_output = (err, stats) => {
      let to_print;
      if (err) {
        to_print = err.stack || err;

        if (err.details) {
          to_print += '\n' + err.details;
        }
      }
      else {
        to_print = stats.toString(verbose ? verbose_opts : normal_opts)
      }

      const was_spinning = spinner.isSpinning;
      if (was_spinning) spinner.stop();
      if (to_print) {
        console.log(to_print);
      }
      if (was_spinning) spinner.start();
    };

    if (settings['watch']) {
      compiler.watch({}, handle_output);
    }
    else {
      compiler.run(handle_output);
    }

    compiler.apply(
        new webpack.ProgressPlugin((handler) => {
          if (handler === 0) {
            spinner.start();
          }
          if (handler === 1) {
            spinner.succeed(settings['page name'] + '  ( ' + timeStamp() + ' )');
            spinner.stop()
          }
        })
    );
  }
}

function timeStamp() {
  // Create a date object with the current time
  const now = new Date();

  // Create an array with the current hour, minute and second
  const time = [now.getHours(), now.getMinutes(), now.getSeconds()];

  // Determine AM or PM suffix based on the hour
  const suffix = (time[0] < 12) ? "AM" : "PM";

  // Convert hour from military time
  time[0] = (time[0] < 12) ? time[0] : time[0] - 12;

  // If hour is 0, set it to 12
  time[0] = time[0] || 12;

  // If seconds and minutes are less than 10, add a zero
  for (let i = 1; i < 3; i++) {
    if (time[i] < 10) {
      time[i] = "0" + time[i];
    }
  }

  // Return the formatted string
  return time.join(":") + " " + suffix;
}