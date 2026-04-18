import ChatWindow from './ChatWindow';

export default function SimulationView({ switchView }) {
  return <ChatWindow isSimulationMode switchView={switchView} />;
}
