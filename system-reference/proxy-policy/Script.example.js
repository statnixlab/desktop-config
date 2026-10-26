// Sanitized reference only. Replace connection fields and subscription URLs locally.
// This file is intentionally excluded from automatic restore.
function main(config) {
  // This standalone profile owns its node sources and rule layout.
  if (config["proxy-providers"] && config["proxy-providers"]["combined-panstar"]) {
    return config;
  }

  config = config || {};
  config.proxies = Array.isArray(config.proxies) ? config.proxies : [];
  config["proxy-groups"] = Array.isArray(config["proxy-groups"])
    ? config["proxy-groups"]
    : [];

  var myNodes = [
    {
      name: "VPS-Hysteria2",
      type: "hysteria2",
      server: "REPLACE_LOCALLY",
      port: 8443,
      password: "REPLACE_LOCALLY",
      sni: "www.bing.com",
      "skip-cert-verify": true,
      udp: true
    },
    {
      "name": "VPS-Reality",
      "type": "vless",
      "server": "REPLACE_LOCALLY",
      "port": 8443,
      "uuid": "REPLACE_LOCALLY",
      "network": "tcp",
      "udp": true,
      "tls": true,
      "flow": "xtls-rprx-vision",
      "servername": "www.cloudflare.com",
      "client-fingerprint": "REPLACE_LOCALLY",
      "reality-opts": {
        "public-key": "REPLACE_LOCALLY",
        "short-id": "REPLACE_LOCALLY"
      }
    }];

  var myNodeNames = myNodes.map(function (node) {
    return node.name;
  });

  var removeGroupNames = [
    "中转选择",
    "出口选择"
  ];

  var importedProviders = {
    "external-peiqian": {
      type: "http",
      url: "https://example.invalid/subscription",
      path: "./proxy_providers/external-peiqian.yaml",
      interval: 86400,
      proxy: "DIRECT",
      header: {
        "User-Agent": ["Clash.Meta"]
      },
      "health-check": {
        enable: true,
        url: "https://www.gstatic.com/generate_204",
        interval: 600,
        lazy: true
      },
      override: {
        "additional-prefix": "[赔钱机场] "
      }
    },
    "external-baokemeng": {
      type: "http",
      url: "https://example.invalid/subscription",
      path: "./proxy_providers/external-baokemeng.yaml",
      interval: 86400,
      proxy: "DIRECT",
      header: {
        "User-Agent": ["Clash.Meta"]
      },
      "health-check": {
        enable: true,
        url: "https://www.gstatic.com/generate_204",
        interval: 600,
        lazy: true
      },
      override: {
        "additional-prefix": "[宝可梦] "
      }
    },
    "external-edgetunnel": {
      type: "http",
      url: "https://example.invalid/subscription",
      path: "./proxy_providers/external-edgetunnel.yaml",
      interval: 10800,
      proxy: "DIRECT",
      header: {
        "User-Agent": ["Clash.Meta"]
      },
      "health-check": {
        enable: true,
        url: "https://www.gstatic.com/generate_204",
        interval: 600,
        lazy: true
      },
      override: {
        "additional-prefix": "[edgetunnel] "
      }
    }
  };
  var importedProviderNames = Object.keys(importedProviders);

  config["proxy-providers"] =
    config["proxy-providers"] &&
    typeof config["proxy-providers"] === "object"
      ? config["proxy-providers"]
      : {};

  for (var providerIndex = 0; providerIndex < importedProviderNames.length; providerIndex++) {
    var providerName = importedProviderNames[providerIndex];
    config["proxy-providers"][providerName] = importedProviders[providerName];
  }

  // 删除旧的同名自定义节点，再重新加入，避免重复
  config.proxies = config.proxies.filter(function (proxy) {
    return proxy && myNodeNames.indexOf(proxy.name) === -1;
  }).concat(myNodes);

  // 删除不需要的策略组
  config["proxy-groups"] = config["proxy-groups"].filter(function (group) {
    return group && removeGroupNames.indexOf(group.name) === -1;
  });

  var mainGroupName =
    config["proxy-groups"].length > 0 && config["proxy-groups"][0]
      ? config["proxy-groups"][0].name
      : null;

  if (mainGroupName) {
    for (var routeIndex = 0; routeIndex < importedProviderNames.length; routeIndex++) {
      config["proxy-providers"][importedProviderNames[routeIndex]].proxy =
        mainGroupName;
    }
  }

  for (var i = 0; i < config["proxy-groups"].length; i++) {
    var group = config["proxy-groups"][i];

    if (!group || !Array.isArray(group.proxies)) {
      continue;
    }

    // 删除旧节点和已删除策略组引用
    group.proxies = group.proxies.filter(function (name) {
      return (
        myNodeNames.indexOf(name) === -1 &&
        removeGroupNames.indexOf(name) === -1
      );
    });

    // Add custom nodes to the subscription's main, AI, and node-selection groups.
    if (
      group.name &&
      (group.name === mainGroupName ||
        group.name.indexOf("AI服务") !== -1 ||
        group.name.indexOf("节点选择") !== -1)
    ) {
      group.proxies = myNodeNames.concat(group.proxies);
    }

    // Make Peiqian provider nodes selectable in AI service groups.
    if (group.name && group.name.indexOf("AI服务") !== -1) {
      group.use = Array.isArray(group.use) ? group.use : [];
      if (group.use.indexOf("external-peiqian") === -1) {
        group.use.push("external-peiqian");
      }
    }

    if (group.name === mainGroupName) {
      group.use = Array.isArray(group.use)
        ? group.use.filter(function (name) {
            return importedProviderNames.indexOf(name) === -1;
          })
        : [];
      group.use = importedProviderNames.concat(group.use);
    }
  }

  // Keep management connections to this proxy server direct.
  var awsDirectRules = [
    "IP-CIDR,192.0.2.1/32,DIRECT,no-resolve",
    "DOMAIN,proxy.example.invalid,DIRECT"
  ];
  config.rules = awsDirectRules.concat((config.rules || []).filter(function (rule) {
    return awsDirectRules.indexOf(rule) === -1;
  }));
  return config;
}
