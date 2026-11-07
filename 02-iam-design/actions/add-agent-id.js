exports.onExecutePostLogin = async (event, api) => {
  const agentId = (event.user.app_metadata && event.user.app_metadata.agent_id) || 'agent-001';
  api.idToken.setCustomClaim('agent_id', agentId);
  api.accessToken.setCustomClaim('agent_id', agentId);
  api.accessToken.setCustomClaim('https://securenova.local/agent_id', agentId);
};
