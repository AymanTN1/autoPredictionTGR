#!/bin/bash
#
# 🚀 EXEMPLES CURL - API Prédiction v2.0 Sécurisée
#
# Avant de lancer ces commandes, assurez-vous que :
# 1. L'API est en cours d'exécution : python -m uvicorn main:app --reload
# 2. Vous avez un fichier CSV à tester : dataSets/depensesEtat.csv
# 3. Vous êtes dans le répertoire du projet
#

API_URL="http://localhost:8000"
API_KEY="TGR-SECRET-KEY-12345"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║       🚀 EXEMPLES CURL - API Prédiction v2.0 Sécurisée             ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Assurez-vous que l'API est en cours d'exécution :"
echo "   python -m uvicorn main:app --reload"
echo ""
echo "📋 Tests disponibles :"
echo "   1. Health Check (public)"
echo "   2. API Info (public)"
echo "   3. Prédiction MODE AUTO (🔒 Requiert clé API)"
echo "   4. Prédiction MODE UTILISATEUR avec 12 mois (🔒 Requiert clé API)"
echo "   5. Prédiction MODE UTILISATEUR avec 36 mois (🔒 Requiert clé API)"
echo "   6. Prédiction SANS clé API (test sécurité)"
echo ""
echo "═════════════════════════════════════════════════════════════════════"

# ═════════════════════════════════════════════════════════════════════════
# TEST 1️⃣  : HEALTH CHECK (PUBLIC)
# ═════════════════════════════════════════════════════════════════════════

function test_health() {
    echo ""
    echo "🧪 TEST 1 : HEALTH CHECK (Public - Pas de clé requise)"
    echo "──────────────────────────────────────────────────────"
    echo "curl ${API_URL}/health"
    echo ""
    
    curl -s "${API_URL}/health" | python -m json.tool
    echo ""
}

# ═════════════════════════════════════════════════════════════════════════
# TEST 2️⃣  : API INFO (PUBLIC)
# ═════════════════════════════════════════════════════════════════════════

function test_info() {
    echo ""
    echo "🧪 TEST 2 : API INFO (Public - Pas de clé requise)"
    echo "────────────────────────────────────────────────────"
    echo "curl ${API_URL}/info"
    echo ""
    
    curl -s "${API_URL}/info" | python -m json.tool | head -30
    echo "   ... (output truncated)"
    echo ""
}

# ═════════════════════════════════════════════════════════════════════════
# TEST 3️⃣  : MODE AUTO (SMART DURATION)
# ═════════════════════════════════════════════════════════════════════════

function test_auto() {
    echo ""
    echo "🧪 TEST 3 : PRÉDICTION MODE AUTO (Smart Duration)"
    echo "─────────────────────────────────────────────────"
    echo "Commande :"
    echo "curl -X POST ${API_URL}/predict/auto \\"
    echo "  -H \"X-API-Key: ${API_KEY}\" \\"
    echo "  -F \"file=@dataSets/depensesEtat.csv\""
    echo ""
    echo "Réponse :"
    
    curl -s -X POST "${API_URL}/predict/auto" \
        -H "X-API-Key: ${API_KEY}" \
        -F "file=@dataSets/depensesEtat.csv" | python -m json.tool | head -50
    echo "   ... (output truncated)"
    echo ""
}

# ═════════════════════════════════════════════════════════════════════════
# TEST 4️⃣  : MODE UTILISATEUR (12 MOIS - APPROUVÉ)
# ═════════════════════════════════════════════════════════════════════════

function test_user_12() {
    echo ""
    echo "🧪 TEST 4 : PRÉDICTION MODE UTILISATEUR (12 mois - Probable approuvé)"
    echo "───────────────────────────────────────────────────────────────────"
    echo "Commande :"
    echo "curl -X POST ${API_URL}/predict \\"
    echo "  -H \"X-API-Key: ${API_KEY}\" \\"
    echo "  -F \"file=@dataSets/depensesEtat.csv\" \\"
    echo "  -F \"months=12\""
    echo ""
    echo "Réponse (extrait) :"
    
    curl -s -X POST "${API_URL}/predict" \
        -H "X-API-Key: ${API_KEY}" \
        -F "file=@dataSets/depensesEtat.csv" \
        -F "months=12" | python -m json.tool | head -50
    echo "   ... (output truncated)"
    echo ""
}

# ═════════════════════════════════════════════════════════════════════════
# TEST 5️⃣  : MODE UTILISATEUR (36 MOIS - PEUT ÊTRE RÉDUIT)
# ═════════════════════════════════════════════════════════════════════════

function test_user_36() {
    echo ""
    echo "🧪 TEST 5 : PRÉDICTION MODE UTILISATEUR (36 mois - Peut être réduit)"
    echo "──────────────────────────────────────────────────────────────────────"
    echo "Commande :"
    echo "curl -X POST ${API_URL}/predict \\"
    echo "  -H \"X-API-Key: ${API_KEY}\" \\"
    echo "  -F \"file=@dataSets/depensesEtat.csv\" \\"
    echo "  -F \"months=36\""
    echo ""
    echo "Réponse (extrait) :"
    
    curl -s -X POST "${API_URL}/predict" \
        -H "X-API-Key: ${API_KEY}" \
        -F "file=@dataSets/depensesEtat.csv" \
        -F "months=36" | python -m json.tool | head -50
    echo "   ... (output truncated)"
    echo ""
}

# ═════════════════════════════════════════════════════════════════════════
# TEST 6️⃣  : SÉCURITÉ - CLÉ INVALIDE
# ═════════════════════════════════════════════════════════════════════════

function test_security() {
    echo ""
    echo "🔒 TEST 6 : SÉCURITÉ - Accès SANS clé API valide"
    echo "───────────────────────────────────────────────────"
    echo "Commande (CLÉ INVALIDE) :"
    echo "curl -X POST ${API_URL}/predict \\"
    echo "  -H \"X-API-Key: INVALID-KEY-123\" \\"
    echo "  -F \"file=@dataSets/depensesEtat.csv\""
    echo ""
    echo "Réponse attendue : 401 Unauthorized"
    echo ""
    
    curl -s -X POST "${API_URL}/predict" \
        -H "X-API-Key: INVALID-KEY-123" \
        -F "file=@dataSets/depensesEtat.csv" | python -m json.tool
    echo ""
}

# ═════════════════════════════════════════════════════════════════════════
# MENU PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════

function main() {
    if [ $# -eq 0 ]; then
        echo ""
        echo "Usage : $0 [numéro_test | all]"
        echo ""
        echo "Numéros de test disponibles :"
        echo "  1   : Health Check"
        echo "  2   : API Info"
        echo "  3   : MODE AUTO"
        echo "  4   : MODE UTILISATEUR (12 mois)"
        echo "  5   : MODE UTILISATEUR (36 mois)"
        echo "  6   : Sécurité (clé invalide)"
        echo "  all : Tous les tests"
        echo ""
        return
    fi
    
    case "$1" in
        1)
            test_health
            ;;
        2)
            test_info
            ;;
        3)
            test_auto
            ;;
        4)
            test_user_12
            ;;
        5)
            test_user_36
            ;;
        6)
            test_security
            ;;
        all)
            test_health
            test_info
            test_auto
            test_user_12
            test_user_36
            test_security
            echo "════════════════════════════════════════════════════════════════════"
            echo "✅ TOUS LES TESTS TERMINÉS !"
            echo "════════════════════════════════════════════════════════════════════"
            ;;
        *)
            echo "❌ Numéro de test invalide : $1"
            echo "   Utilisez : 1, 2, 3, 4, 5, 6, ou all"
            ;;
    esac
}

# Appeler main avec arguments
main "$@"
