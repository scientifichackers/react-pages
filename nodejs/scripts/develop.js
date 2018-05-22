#!/usr/bin/env node
'use strict';

process.env.BABEL_ENV = 'development';
process.env.NODE_ENV = 'development';

const util = require('util');
const get_config = require('../config/webpack.config.dev');
const cli = require('commander');
const webpack = require('webpack');

cli
    .arguments('[json_cmd]')
    .action(develop)
    .parse(process.argv); // end with parse to parse through the input

function develop(json_cmd) {
    const cmd = JSON.parse(json_cmd);

    if (verify_cmd(cmd)) {
        const config = get_config(cmd);

        console.debug('webpack config:', util.inspect(config, false, null));

        const compiler = webpack(config);

        if (cmd['watch']) {
            compiler.watch({}, handle_output);
        }
        else {
            compiler.run(handle_output);
        }
    }
    else {
        console.error('Bad command!');
        process.exit(1)
    }
}


function verify_cmd(cmd) {
    // verify whether the command has required parameters or not
    for (const param of ['src', 'dest dir', 'watch', 'npm root', 'src dir', 'html_template']) {
        if (!cmd.hasOwnProperty(param)) {
            return false
        }
    }
    return true
}

//
// function remove_plugin(plugins, to_remove) {
//     // remove a plugin from a list of plugins
//     return plugins.filter(plugin => !(plugin instanceof to_remove))
// }
//
// function update(dict, update) {
//     // simulate python's dict.update()
//     return Object.assign(dict, update);
// }

function handle_output(err, stats) {
    // handle webpack output and print out in proper format
    if (err) {
        console.error(err.stack || err);
        if (err.details) {
            console.error(err.details);
        }
        return;
    }

    // const info = stats.toJson();
    //
    // if (stats.hasErrors()) {
    //     console.error(info.errors);
    // }
    //
    // if (stats.hasWarnings()) {
    //     console.warn(info.warnings);
    // }

    console.log(
        stats.toString({
            chunks: false,
            colors: true,
        })
    );
}