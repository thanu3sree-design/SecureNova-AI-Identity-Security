exports.onExecutePostLogin = async (event, api) => {
  const risk = Number((event.user.app_metadata && event.user.app_metadata.risk_score) || 0);
  if (risk >= 80) {
    api.access.deny('SecureNova risk policy: login blocked (risk score ' + risk + ').');
  }
};
