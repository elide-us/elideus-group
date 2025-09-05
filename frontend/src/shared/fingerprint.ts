export const getFingerprint = (): string => {
	let fp = localStorage.getItem('deviceFingerprint');
	if (!fp) {
		fp = crypto.randomUUID();
		localStorage.setItem('deviceFingerprint', fp);
	}
	return fp;
};
