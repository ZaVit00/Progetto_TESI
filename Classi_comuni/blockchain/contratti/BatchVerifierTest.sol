// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

contract BatchVerifier {
    struct BatchInfo {
        string merkle_root;
        string cid_merkle_path;
    }

    mapping(uint256 => BatchInfo) public batches;

    /// @notice Salva o sovrascrive un batch con il relativo merkle_root e cid_merkle_path.
    /// @dev Se esiste già un batch con lo stesso id, viene sovrascritto.
    /// da utilizzare in caso di test per sovrascrivere batch esistenti (SOLO IN CASO DI TEST)
    function salvaBatch(uint256 id, string memory merkle_root, string memory cid_merkle_path) public {
        batches[id] = BatchInfo(merkle_root, ìcid_merkle_path);

    }

    /// @notice Restituisce i dati associati a un batch
    function getBatch(uint256 id) public view returns (string memory, string memory) {
        BatchInfo memory info = batches[id];
        return (info.merkle_root, info.cid_merkle_path);
    }
}
