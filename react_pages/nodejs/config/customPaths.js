'use strict';

module.exports = function get_custom_paths(settings) {
  return {
    appSrc: settings['src dir'],
    appIndexJs: settings['src'],
    appBuild: settings['dest dir'],
    appNodeModules: settings['npm prefix'] , // allows cross-page imports!
    appHtml: settings['html template'],
  }
};