import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
    Alert,
    Box,
    Button,
    Card,
    CardActions,
    CardContent,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    Grid,
    Stack,
    Typography,
} from "@mui/material";
import PageTitle from "../components/PageTitle";
import UserContext from "../shared/UserContext";
import { fetchProfile } from "../rpc/users/profile";
import { fetchList as fetchProductList, fetchPurchase } from "../rpc/users/products";
import type { UsersProductItem1, UsersProductPurchaseResult1 } from "../shared/RpcModels";

type ProductItem = UsersProductItem1 & {
    already_enabled?: boolean;
};

const CATEGORY_ORDER = ["enablement", "credit_purchase"] as const;

const CATEGORY_LABELS: Record<string, { title: string; description: string }> = {
    enablement: {
        title: "Features & Integrations",
        description: "Turn on account capabilities and integrations.",
    },
    credit_purchase: {
        title: "AI Credits",
        description: "Prepaid AI credit packages for usage-based services.",
    },
};

const getErrorMessage = (error: unknown): string => {
    if (typeof error === "object" && error !== null) {
        const response = Reflect.get(error, "response");
        if (typeof response === "object" && response !== null) {
            const data = Reflect.get(response, "data");
            if (typeof data === "object" && data !== null) {
                const detail = Reflect.get(data, "detail");
                if (typeof detail === "string" && detail.trim()) {
                    return detail;
                }
            }
        }
        const message = Reflect.get(error, "message");
        if (typeof message === "string" && message.trim()) {
            return message;
        }
    }
    return "Something went wrong.";
};

const formatPrice = (price: string, currency: string): string => {
    const numeric = Number(price || 0);
    if (!Number.isFinite(numeric) || numeric === 0) {
        return "Free";
    }
    return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency,
        minimumFractionDigits: 2,
    }).format(numeric);
};

const ProductsPage = (): JSX.Element => {
    const { userData } = useContext(UserContext);
    const [products, setProducts] = useState<ProductItem[]>([]);
    const [walletCredits, setWalletCredits] = useState<number>(0);
    const [loading, setLoading] = useState(true);
    const [busySku, setBusySku] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [selectedProduct, setSelectedProduct] = useState<ProductItem | null>(null);

    const loadProducts = useCallback(async (): Promise<void> => {
        const response = await fetchProductList();
        setProducts((response.products || []).sort((left, right) => left.sort_order - right.sort_order));
    }, []);

    const loadWallet = useCallback(async (): Promise<void> => {
        const profile = await fetchProfile();
        setWalletCredits(Number(profile.credits || 0));
    }, []);

    const loadAll = useCallback(async (): Promise<void> => {
        try {
            setLoading(true);
            setErrorMessage(null);
            await Promise.all([loadProducts(), loadWallet()]);
        } catch (error: unknown) {
            setErrorMessage(getErrorMessage(error));
        } finally {
            setLoading(false);
        }
    }, [loadProducts, loadWallet]);

    useEffect(() => {
        if (!userData) {
            return;
        }
        void loadAll();
    }, [loadAll, userData]);

    const groupedProducts = useMemo(() => {
        return CATEGORY_ORDER.map((category) => ({
            category,
            items: products.filter((product) => product.category === category),
        })).filter((group) => group.items.length > 0);
    }, [products]);

    const closeDialog = (): void => {
        setSelectedProduct(null);
    };

    const handlePurchase = async (): Promise<void> => {
        if (!selectedProduct) {
            return;
        }
        try {
            setBusySku(selectedProduct.sku);
            setErrorMessage(null);
            setSuccessMessage(null);
            const result = await fetchPurchase({ sku: selectedProduct.sku }) as UsersProductPurchaseResult1;
            const details: string[] = [];
            if (result.credits_granted) {
                details.push(`${result.credits_granted.toLocaleString()} credits added`);
            }
            if (result.enablement_granted) {
                details.push(`${result.enablement_granted} enabled`);
            }
            if (result.lot_number) {
                details.push(`lot ${result.lot_number}`);
            }
            setSuccessMessage([
                `${selectedProduct.name} purchased successfully.`,
                details.length ? details.join(" • ") : null,
                `Transaction ${result.transaction_token}`,
            ].filter(Boolean).join(" "));
            closeDialog();
            await Promise.all([loadProducts(), loadWallet()]);
        } catch (error: unknown) {
            setErrorMessage(getErrorMessage(error));
        } finally {
            setBusySku(null);
        }
    };

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle>Products &amp; Services</PageTitle>
            <Divider sx={{ mb: 2 }} />

            <Stack spacing={2}>
                <Card variant="outlined">
                    <CardContent>
                        <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between">
                            <Box>
                                <Typography variant="h6">Your wallet</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Purchase credits or enable account capabilities from this catalog.
                                </Typography>
                            </Box>
                            <Chip
                                color="success"
                                label={`Balance: ${walletCredits.toLocaleString()} credits`}
                                sx={{ alignSelf: { xs: "flex-start", md: "center" } }}
                            />
                        </Stack>
                    </CardContent>
                </Card>

                {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
                {successMessage && <Alert severity="success">{successMessage}</Alert>}

                {loading ? (
                    <Typography color="text.secondary">Loading products…</Typography>
                ) : (
                    groupedProducts.map((group) => (
                        <Stack key={group.category} spacing={2}>
                            <Box>
                                <Typography variant="h6">{CATEGORY_LABELS[group.category]?.title || group.category}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    {CATEGORY_LABELS[group.category]?.description || ""}
                                </Typography>
                            </Box>
                            <Grid container spacing={2}>
                                {group.items.map((product) => {
                                    const isEnablement = product.category === "enablement";
                                    const isDisabled = Boolean(product.already_enabled) || busySku === product.sku;
                                    return (
                                        <Grid item xs={12} md={6} xl={4} key={product.sku}>
                                            <Card variant="outlined" sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
                                                <CardContent sx={{ flexGrow: 1 }}>
                                                    <Stack spacing={1.5}>
                                                        <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="flex-start">
                                                            <Box>
                                                                <Typography variant="h6">{product.name}</Typography>
                                                                <Typography variant="caption" color="text.secondary">
                                                                    SKU: {product.sku}
                                                                </Typography>
                                                            </Box>
                                                            <Chip label={formatPrice(product.price, product.currency)} color={Number(product.price) > 0 ? "primary" : "default"} />
                                                        </Stack>
                                                        <Typography variant="body2" color="text.secondary">
                                                            {product.description || "No description available."}
                                                        </Typography>
                                                        {product.credits > 0 && (
                                                            <Chip label={`${product.credits.toLocaleString()} credits`} color="info" variant="outlined" sx={{ width: "fit-content" }} />
                                                        )}
                                                        {product.already_enabled && (
                                                            <Chip label="Already Enabled" color="success" sx={{ width: "fit-content" }} />
                                                        )}
                                                    </Stack>
                                                </CardContent>
                                                <CardActions>
                                                    <Button
                                                        fullWidth
                                                        variant="contained"
                                                        disabled={isDisabled}
                                                        onClick={() => setSelectedProduct(product)}
                                                    >
                                                        {product.already_enabled ? "Already Enabled" : isEnablement ? "Enable" : "Purchase"}
                                                    </Button>
                                                </CardActions>
                                            </Card>
                                        </Grid>
                                    );
                                })}
                            </Grid>
                        </Stack>
                    ))
                )}
            </Stack>

            <Dialog open={Boolean(selectedProduct)} onClose={closeDialog} fullWidth maxWidth="sm">
                <DialogTitle>Confirm purchase</DialogTitle>
                <DialogContent>
                    <Typography>
                        {selectedProduct
                            ? `Purchase ${selectedProduct.name} for ${formatPrice(selectedProduct.price, selectedProduct.currency)}?`
                            : ""}
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={closeDialog}>Cancel</Button>
                    <Button onClick={() => void handlePurchase()} variant="contained" disabled={!selectedProduct || busySku !== null}>
                        Confirm
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ProductsPage;
