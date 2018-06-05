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

    const spinner = ora({'spinner': 'moon'});

    for (const settings of settings_list) {
        spinner.stop();
        console.log(settings['start msg']);
        spinner.start();

        const config = get_custom_config(settings);
        // console.debug('webpack config:', util.inspect(config, false, null));

        const compiler = webpack(config);


        const handle_output = (err, stats) => {
            // handle webpack output and print out in proper format
            if (err) {
                spinner.stop();

                console.error(err.stack || err);
                if (err.details) {
                    console.error(err.details);
                }

                spinner.start();
                return
            }

            if (verbose) {
                spinner.stop();

                console.log();
                console.log(
                    stats.toString({
                        chunks: false,
                        colors: true,
                    })
                );
                console.log();

                spinner.start();
            }
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
                    spinner.stop();
                    console.log(settings['start msg']);
                    spinner.start();
                }
                if (handler === 1) {

                    spinner.succeed(settings['complete msg'])
                }
            })
        );
    }
}