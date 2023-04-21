// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

const organizationName = "louisvdw";
const projectName = "dbus-serialbattery";

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'dbus-serialbattery',
  tagline: 'Venus OS battery driver',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: `https://${organizationName}.github.io`,
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: `/${projectName}/`,

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: organizationName, // Usually your GitHub org/user name.
  projectName: projectName, // Usually your repo name.

  //onBrokenLinks: 'throw',
  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl: 'https://github.com/Louisvdw/dbus-serialbattery/tree/docusaurus/docs/',
          sidebarCollapsible: false
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      algolia: {
        appId: 'BUS7YVLUUB',
        apiKey: '11f8f0c4ceaf5dd684a254191cc007d6',
        indexName: 'dbus-serialbattery',
      },
      //
      colorMode: {
        //defaultMode: 'light',
        //disableSwitch: false,
        respectPrefersColorScheme: true,
      },
      // Replace with your project's social card
      image: 'img/docusaurus-social-card.jpg',
      navbar: {
        title: projectName,
        logo: {
          alt: `${projectName} Logo`,
          src: 'img/logo.svg',
        },
        items: [
          {
            to: '/',
            activeBasePath: 'docs',
            label: 'Docs',
            position: 'left',
          },
          {
            to: '/troubleshoot/faq',
            activeBasePath: 'docs',
            label: 'FAQ',
            position: 'left',
          },
          {
            label: 'GitHub Issues',
            href: `https://github.com/${organizationName}/${projectName}/issues?q=is%3Aissue`,
            position: 'left',
          },
          {
            label: 'GitHub Discussions',
            href: `https://github.com/${organizationName}/${projectName}/discussions?discussions_q=`,
            position: 'left',
          },
          {
            label: 'GitHub',
            href: `https://github.com/${organizationName}/${projectName}`,
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Community',
            items: [
              {
                label: 'GitHub',
                href: `https://github.com/${organizationName}/${projectName}`,
              },
              {
                label: 'GitHub Issues',
                href: `https://github.com/${organizationName}/${projectName}/issues?q=is%3Aissue`,
              },
              {
                label: 'GitHub Discussions',
                href: `https://github.com/${organizationName}/${projectName}/discussions?discussions_q=`,
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} ${organizationName}`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
};

module.exports = config;
