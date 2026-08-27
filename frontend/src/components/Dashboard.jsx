/**
 * Dashboard — Affiche les résultats de l'analyse du relevé bancaire.
 * 
 * Reçoit les données de l'API (transactions + summary) et les affiche
 * sous forme de cartes statistiques, tableau de transactions, et graphique.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

// Couleurs par catégorie
const CATEGORY_COLORS = {
  fixed_charge: '#ef4444',
  variable_expense: '#f97316',
  income: '#22c55e',
  transfer: '#3b82f6',
  debt_payment: '#a855f7',
  other: '#6b7280',
}

const CATEGORY_LABELS = {
  fixed_charge: 'Charges fixes',
  variable_expense: 'Dépenses variables',
  income: 'Revenus',
  transfer: 'Virements',
  debt_payment: 'Paiements dette',
  other: 'Autres',
}

function Dashboard({ data }) {
  const { summary, transactions } = data

  // Prépare les données pour le graphique
  const chartData = Object.entries(summary.top_categories).map(([key, value]) => ({
    name: CATEGORY_LABELS[key] || key,
    amount: Math.abs(value),
    color: CATEGORY_COLORS[key] || '#6b7280',
    original: value,
  }))

  return (
    <div className="mt-8 space-y-6">
      {/* Cartes statistiques */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          label="Revenus"
          value={`$${summary.total_income.toLocaleString('fr-CA', { minimumFractionDigits: 2 })}`}
          color="text-green-600"
          bg="bg-green-50"
        />
        <StatCard
          label="Dépenses"
          value={`$${Math.abs(summary.total_expenses).toLocaleString('fr-CA', { minimumFractionDigits: 2 })}`}
          color="text-red-600"
          bg="bg-red-50"
        />
        <StatCard
          label="Charges fixes"
          value={`$${Math.abs(summary.fixed_charges_total).toLocaleString('fr-CA', { minimumFractionDigits: 2 })}`}
          color="text-orange-600"
          bg="bg-orange-50"
        />
        <StatCard
          label="Balance nette"
          value={`$${summary.net_balance.toLocaleString('fr-CA', { minimumFractionDigits: 2 })}`}
          color={summary.net_balance >= 0 ? 'text-green-600' : 'text-red-600'}
          bg={summary.net_balance >= 0 ? 'bg-green-50' : 'bg-red-50'}
        />
      </div>

      {/* Graphique par catégorie */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Répartition par catégorie</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip formatter={(v) => `$${v.toFixed(2)}`} />
            <Bar dataKey="amount" radius={[6, 6, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Tableau des transactions */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">
            Transactions ({transactions.length})
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-3 text-left">Date</th>
                <th className="px-4 py-3 text-left">Description</th>
                <th className="px-4 py-3 text-right">Montant</th>
                <th className="px-4 py-3 text-left">Catégorie</th>
                <th className="px-4 py-3 text-center">Confiance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {transactions.map((t, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-600">{t.date}</td>
                  <td className="px-4 py-3 text-gray-800 font-medium">{t.description}</td>
                  <td className={`px-4 py-3 text-right font-mono font-medium ${t.amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {t.amount >= 0 ? '+' : ''}{t.amount.toFixed(2)} $
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="px-2 py-1 rounded-full text-xs font-medium"
                      style={{
                        backgroundColor: CATEGORY_COLORS[t.category] + '20',
                        color: CATEGORY_COLORS[t.category],
                      }}
                    >
                      {CATEGORY_LABELS[t.category] || t.category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-xs font-medium ${t.confidence > 0.8 ? 'text-green-600' : t.confidence > 0.5 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {(t.confidence * 100).toFixed(0)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, color, bg }) {
  return (
    <div className={`${bg} rounded-xl p-5 border border-gray-100`}>
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  )
}

export default Dashboard
